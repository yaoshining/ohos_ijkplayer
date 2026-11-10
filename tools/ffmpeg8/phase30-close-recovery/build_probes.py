"""Relink two standalone fault probes from a completed Phase30 A candidate build."""
import argparse
import hashlib
from pathlib import Path
import shlex
import subprocess

HERE = Path(__file__).resolve().parent
CANDIDATE = "b1638535c6c13786110ce2b7bc0758e5c0b89355d63929763bfb58891a0e7ae4"

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("build", type=Path, help="configured FFmpeg build with src/ and toolchain/")
    parser.add_argument("output", type=Path, help="new output directory")
    args = parser.parse_args()
    build = args.build.resolve()
    unit = "src/libavcodec/ohdec.c"
    source = (build / unit).read_bytes()
    if hashlib.sha256(source).hexdigest() != CANDIDATE:
        raise SystemExit("unexpected candidate source")
    library = "libavcodec/libavcodec.so.62"
    preview = subprocess.check_output(["make", "-n", "-W", unit, "V=1", "REVISION=8.0", library],
                                      cwd=build, text=True).splitlines()
    compile_cmd, = [shlex.split(line) for line in preview if line.endswith(" " + unit)]
    link_cmd, = [shlex.split(line) for line in preview if " -shared " in line and "@" + library + ".objs" in line]
    objects, = [shlex.split(line)[1:-2] for line in preview if line.startswith("echo ") and line.endswith(library + ".objs")]
    source = source.decode()
    signature = "static av_cold int oh_decode_close("
    pre, close = source.split(signature)
    for old, new in [("stop_err = OH_VideoDecoder_Stop(s->dec);", "stop_err = probe_close_call(ref, false);"),
                     ("destroy_err = OH_VideoDecoder_Destroy(s->dec);", "destroy_err = probe_close_call(ref, true);")]:
        assert close.count(old) == 1
        close = close.replace(old, new)
    surface = 'p30_codec_trace(avctx, oh_decode_ref(s), "surface-end", err);'
    assert pre.count(surface) == 1
    pre = pre.replace(surface, surface + '''
        OH_LOG_Print(LOG_APP, LOG_INFO, 0xD001, "CloseVerify", "op=set rc=%{public}d decoder=%{public}llu surface=%{public}llu",
                     err, (unsigned long long)oh_decode_ref(s)->trace_instance, (unsigned long long)oh_decode_ref(s)->surface_id);''')
    pre = pre.replace('#include "config_components.h"', '#include "config_components.h"\n#include <hilog/log.h>')
    parent = args.output.resolve()
    parent.mkdir(parents=True, exist_ok=False)
    for mode in ("stop", "destroy"):
        out = parent / mode
        out.mkdir()
        c = out / "ohdec.c"
        c.write_text(pre + (HERE / "probe.h").read_text() + signature + close)
        obj = out / "ohdec.o"
        lib = out / "libavcodec.so.62"
        paths = {unit: c, "libavcodec/ohdec.o": obj, "libavcodec/ohdec.d": out / "ohdec.d"}
        cmd = [paths.get(v, v) for v in compile_cmd]
        subprocess.run(cmd + ["-iquote", "src/libavcodec", f"-DPROBE_DESTROY={int(mode == 'destroy')}"], cwd=build, check=True)
        rsp = out / "objects.rsp"
        assert objects.count("libavcodec/ohdec.o") == 1
        rsp.write_text("\n".join(str(obj) if o == "libavcodec/ohdec.o" else o for o in objects))
        paths = {library: lib, "@" + library + ".objs": "@" + str(rsp)}
        subprocess.run([paths.get(v, v) for v in link_cmd] + ["-lhilog_ndk.z"], cwd=build, check=True)
        subprocess.run(["toolchain/llvm/bin/llvm-strip", lib], cwd=build, check=True)

if __name__ == "__main__":
    main()
