#!/usr/bin/env python3
"""T008 runner: compile and execute real ohdec lifecycle slices."""
import argparse, hashlib, json, os, shutil, subprocess, sys
from pathlib import Path
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
CASES = ["close-held-frame", "callback-after-close", "token-close-race",
         "callback-inflight-close", "prepare-fail", "duplicate-close"]
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", choices=["baseline", "phase28"], required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    out = Path(args.out)
    if out.exists(): raise SystemExit("refusing to overwrite: %s" % out)
    out.mkdir(parents=True)
    ex = out / "extracted"
    r = subprocess.run([sys.executable, "-B", str(HERE/"extract.py"), "--source",
                        args.source, "--kind", "ffmpeg", "--out", str(ex)],
                       capture_output=True, text=True)
    (out/"extract.log").write_text(r.stdout+r.stderr)
    if r.returncode: raise SystemExit(r.returncode)
    shutil.copy2(HERE/"ohdec"/"harness.c", out/"harness.c")
    define = "-DBASELINE" if args.source == "baseline" else "-DPHASE28"
    cmd = ["clang", "-std=c11", "-D_POSIX_C_SOURCE=200809L", define,
           "-Wall", "-Wextra", "-Werror", "-Wno-unused-function",
           "-Wno-unused-parameter", "-Wno-unused-but-set-variable", "-Wno-sign-compare", "-g", "-O0",
           "-I", str(out), "-I", str(ex), str(out/"harness.c"),
           "-o", str(out/"harness"), "-pthread"]
    c = subprocess.run(cmd, capture_output=True, text=True)
    (out/"compile.log").write_text(c.stdout+c.stderr)
    binding = json.loads((ex/"source-binding.json").read_text())
    result = {"task":"T008","source":args.source,
              "mode":"RED" if args.source=="baseline" else "GREEN",
              "compileCommand":cmd,"compileExit":c.returncode,
              "sourceBinding":binding,"cases":[],"accepted":False}
    if c.returncode:
        (out/"results.json").write_text(json.dumps(result,indent=2)+"\n")
        print("COMPILE FAILURE; not accepted as RED")
        raise SystemExit(c.returncode)
    ok = True
    for case in CASES:
        env = dict(os.environ)
        try:
            p = subprocess.run([str(out/"harness"), case], capture_output=True,
                               text=True, timeout=30, env=env)
            code, stdout, stderr = p.returncode, p.stdout, p.stderr
        except subprocess.TimeoutExpired as e:
            code = 124; stdout = ""; stderr = "TIMEOUT"
        (out/(case+".log")).write_text(stdout+stderr)
        failure = ("FAIL" in stdout) or code != 0
        expected = (args.source=="baseline" and failure) or (args.source=="phase28" and not failure)
        ok = ok and expected
        result["cases"].append({"case":case,"exitCode":code,"stdout":stdout,
                                "stderr":stderr,"semanticFailure":failure,
                                "expected":expected})
        print("%-30s exit=%s semantic_failure=%s expected=%s" % (case,code,failure,expected))
    result["accepted"] = ok
    (out/"results.json").write_text(json.dumps(result,indent=2)+"\n")
    print("ACCEPTED" if ok else "NOT ACCEPTED")
    raise SystemExit(0 if ok else 1)
if __name__ == "__main__":
    main()
