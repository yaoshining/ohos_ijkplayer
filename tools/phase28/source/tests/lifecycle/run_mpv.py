#!/usr/bin/env python3
"""T005 runner: compile and execute real mpv lifecycle slices.

Baseline mode requires every case to compile and then report a semantic FAIL.
Phase28 mode requires every case to PASS. A compile error is never accepted as
RED. Each run records source binding, exact compile command, logs and timeout.
"""
import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
CASES = ["mapper-uninit-order", "vd-lavc-preflight",
         "vd-lavc-preflight-uninit", "vo-drain-control", "eof-deferred", "surface-invalid-reinit", "empty-current-drain"]


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", choices=["baseline", "phase28"], required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    out = Path(args.out)
    if out.exists():
        raise SystemExit("refusing to overwrite existing run root: %s" % out)
    out.mkdir(parents=True)
    extract_dir = out / "extracted"
    r = subprocess.run([sys.executable, "-B", str(HERE / "extract.py"),
                        "--source", args.source, "--kind", "mpv",
                        "--out", str(extract_dir)],
                       capture_output=True, text=True)
    (out / "extract.log").write_text(r.stdout + r.stderr)
    if r.returncode:
        raise SystemExit(r.returncode)
    shutil.copy2(HERE / "mpv" / "harness.c", out / "harness.c")

    define = "-DBASELINE" if args.source == "baseline" else "-DPHASE28"
    cmd = ["clang", "-std=c11", "-D_POSIX_C_SOURCE=200809L", define,
           "-Wall", "-Wextra", "-Werror", "-Wno-unused-function",
           "-Wno-unused-parameter", "-Wno-unused-but-set-variable", "-g", "-O0",
           "-fsanitize=address,undefined", "-fno-omit-frame-pointer",
           "-I", str(out), "-I", str(extract_dir),
           str(out / "harness.c"), "-o", str(out / "harness")]
    c = subprocess.run(cmd, capture_output=True, text=True)
    (out / "compile.log").write_text(c.stdout + c.stderr)
    binding = json.loads((extract_dir / "source-binding.json").read_text())
    result = {
        "task": "T005",
        "source": args.source,
        "mode": "RED" if args.source == "baseline" else "GREEN",
        "compileCommand": cmd,
        "compileExit": c.returncode,
        "sourceBinding": binding,
        "cases": [],
        "accepted": False,
    }
    if c.returncode:
        (out / "results.json").write_text(json.dumps(result, indent=2) + "\n")
        print("COMPILE FAILURE; not accepted as RED")
        raise SystemExit(c.returncode)

    ok = True
    for case in CASES:
        env = dict(os.environ, ASAN_OPTIONS="halt_on_error=1:detect_leaks=0",
                   UBSAN_OPTIONS="halt_on_error=1:print_stacktrace=1")
        try:
            p = subprocess.run([str(out / "harness"), case], capture_output=True,
                               text=True, timeout=30, env=env)
            code, stdout, stderr = p.returncode, p.stdout, p.stderr
        except subprocess.TimeoutExpired as e:
            code = 124
            stdout = (e.stdout or b"").decode() if isinstance(e.stdout, bytes) else (e.stdout or "")
            stderr = "TIMEOUT"
        (out / (case + ".log")).write_text(stdout + stderr)
        failure = ("FAIL" in stdout) or code != 0
        expected = (args.source == "baseline" and failure) or \
                   (args.source == "phase28" and not failure)
        ok = ok and expected
        result["cases"].append({
            "case": case,
            "exitCode": code,
            "stdout": stdout,
            "stderr": stderr,
            "semanticFailure": failure,
            "expected": expected,
        })
        print("%-30s exit=%s semantic_failure=%s expected=%s" %
              (case, code, failure, expected))
    result["accepted"] = ok
    (out / "results.json").write_text(json.dumps(result, indent=2) + "\n")
    print("ACCEPTED" if ok else "NOT ACCEPTED")
    raise SystemExit(0 if ok else 1)


if __name__ == "__main__":
    main()
