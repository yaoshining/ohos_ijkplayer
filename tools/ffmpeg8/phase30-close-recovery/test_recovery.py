"""Run the archived lifecycle doubles against the original and patched A functions."""
import hashlib
import os
from pathlib import Path
import subprocess
import sys
import tempfile

HERE = Path(__file__).resolve().parent
TEST = HERE / "tests"
SOURCE = TEST / "baseline-ohdec.c"
EXPECTED = "d7c4bcc960d54dcae930168a56fcd6cf2b064e8758294b9e6a98c80768f19499"

def run(work, original):
    root = work / "source"
    unit = root / "libavcodec/ohdec.c"
    unit.parent.mkdir(parents=True)
    unit.write_bytes(SOURCE.read_bytes())
    if not original:
        subprocess.run(["patch", "-p1", "-i", str(HERE / "recover.patch")], cwd=root, check=True)
    out = work / "slices"
    env = dict(os.environ, PHASE28_FFMPEG_ROOT=str(root))
    subprocess.run([sys.executable, "-B", str(TEST / "extract.py"), "--source", "phase28",
                    "--kind", "ffmpeg", "--out", str(out)], env=env, check=True)

    code = unit.read_text()
    harness = (TEST / "harness.c").read_text()
    # Use the exact ref layout and reservation helpers, including the registry.
    start = "typedef struct OHCodecDecRef"
    end = "typedef struct OHCodecDecContext"
    window_doubles = """
struct test_window { uint64_t id; int refs; };
static struct test_window old_window = {17}, alias_window = {17}, new_window = {18};
static int OH_NativeWindow_GetSurfaceId(void *w, uint64_t *id) {
    *id = ((struct test_window *)w)->id; return 0;
}
static int OH_NativeWindow_NativeObjectReference(void *w) {
    ((struct test_window *)w)->refs++; return 0;
}
static int OH_NativeWindow_NativeObjectUnreference(void *w) {
    ((struct test_window *)w)->refs--; return 0;
}
#define AV_MUTEX_INITIALIZER { PTHREAD_MUTEX_INITIALIZER }
"""
    left = harness.index("static int OH_NativeWindow_GetSurfaceId")
    right = harness.index("#ifdef MP_OHCODEC_DIAGNOSTIC", left)
    harness = harness[:left] + harness[right:]
    harness = (harness[:harness.index(start)] + window_doubles +
               code[code.index(start):code.index(end)] + harness[harness.index(end):])
    harness = harness.replace("static int stop_result", "static void (*on_injected_error)(void);\nstatic int stop_result")
    for api in ("stop", "destroy"):
        harness = harness.replace(f"return {api}_result;",
                                  f"if ({api}_result && on_injected_error) on_injected_error(); return {api}_result;")
    helper = "static OH_AVErrCode OH_VideoDecoder_RenderOutputBuffer"
    harness = harness.replace(helper, "static OH_AVCodec *last_render_dec;\n"
                              "static uint32_t last_render_index;\n" + helper)
    harness = harness.replace("ev(EV_RENDER_BEGIN);", "last_render_dec = dec; last_render_index = index; ev(EV_RENDER_BEGIN);")
    harness = harness.replace("if (oh_decode_create(e->s, &e->avctx) < 0)\n"
                              "        return -1;",
                              "int create_rc = oh_decode_create(e->s, &e->avctx);\n"
                              "    if (create_rc < 0) return create_rc;")
    # Replace obsolete expectations. Keep the six other lifecycle cases.
    harness = harness[:harness.index("static int mode_consumer_handoff")] + (HERE / "recovery-case.c").read_text() + harness[harness.index("int main("):]
    harness = harness.replace('if (!strcmp(argv[1], "consumer-handoff")) return mode_consumer_handoff();', '')
    for kind in ("stop", "destroy"):
        harness = harness.replace("return mode_" + kind + "_fail();",
                                  f"return test_recovery({int(kind == 'destroy')}, {int(original)});")
    c = work / "test.c"
    c.write_text(harness)
    exe = work / "test"
    subprocess.run(["clang", "-std=c11", "-g", "-fsanitize=address,undefined", "-DPHASE28",
                    "-I", str(out), str(c), "-pthread", "-o", str(exe)], check=True)
    for case in ("stop-fail", "destroy-fail", "token-close-race", "callback-inflight-close",
                 "callback-after-close", "duplicate-close", "prepare-fail", "close-held-frame"):
        subprocess.run([str(exe), case], check=True, timeout=15,
                       env=dict(os.environ, ASAN_OPTIONS="detect_leaks=0",
                                UBSAN_OPTIONS="halt_on_error=1"))

if __name__ == "__main__":
    if hashlib.sha256(SOURCE.read_bytes()).hexdigest() != EXPECTED:
        raise SystemExit("Phase30 A source digest mismatch")
    with tempfile.TemporaryDirectory() as tmp:
        for name in ("original", "candidate"):
            print(name, flush=True)
            run(Path(tmp) / name, name == "original")
