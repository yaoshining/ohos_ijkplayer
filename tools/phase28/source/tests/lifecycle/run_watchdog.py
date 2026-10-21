#!/usr/bin/env python3
"""T011: experiment macro fail-stop and external host watchdog evidence.

The watchdog here is the host subprocess timeout, outside the test worker. It
proves bounded termination of a hung diagnostic process, not product recovery.
"""
import argparse, json, os, shutil, subprocess, sys
from pathlib import Path
HERE = Path(__file__).resolve().parent

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    out = Path(args.out)
    if out.exists(): raise SystemExit("refusing to overwrite: %s" % out)
    out.mkdir(parents=True)
    ex = out/"extracted"
    r = subprocess.run([sys.executable,"-B",str(HERE/"extract.py"),"--source",
                        "phase28","--kind","mpv","--out",str(ex)],
                       capture_output=True,text=True)
    (out/"extract.log").write_text(r.stdout+r.stderr)
    if r.returncode: raise SystemExit(r.returncode)
    shutil.copy2(HERE/"mpv"/"harness.c", out/"harness.c")
    binds = json.loads((ex/"source-binding.json").read_text())
    results = {"task":"T011","source":"phase28","sourceBinding":binds,
               "note":"experiment fail-stop is diagnostic-only; not product recovery",
               "cases":[]}
    for name, define in [("normal", []), ("experiment", ["-DMP_OHCODEC_LIFECYCLE_EXPERIMENT=1"])]:
        binp = out/("harness-"+name)
        cmd = ["clang","-std=c11","-D_POSIX_C_SOURCE=200809L","-DPHASE28",
               "-Wall","-Wextra","-Werror","-Wno-unused-function",
               "-Wno-unused-parameter","-Wno-unused-but-set-variable","-g","-O0",
               *define,"-I",str(out),"-I",str(ex),str(out/"harness.c"),
               "-o",str(binp)]
        c = subprocess.run(cmd,capture_output=True,text=True)
        (out/("compile-"+name+".log")).write_text(c.stdout+c.stderr)
        if c.returncode:
            results["cases"].append({"build":name,"compileExit":c.returncode})
            continue
        def run(case, timeout):
            try:
                p = subprocess.run([str(binp),case],capture_output=True,text=True,
                                   timeout=timeout)
                return p.returncode, p.stdout, p.stderr, False
            except subprocess.TimeoutExpired as e:
                so = e.stdout or ""
                se = e.stderr or ""
                if isinstance(so, bytes): so = so.decode("utf-8", "replace")
                if isinstance(se, bytes): se = se.decode("utf-8", "replace")
                return 124, so, se + "\nTIMEOUT", True
        code, stdout, stderr, timedout = run("unsafe-preflight", 5)
        (out/("run-"+name+"-unsafe.log")).write_text(stdout+stderr)
        if name == "experiment":
            # Only the explicit experiment fail-stop is accepted: SIGABRT
            # (-6/134). A plain FAIL exit, a timeout or any other crash is a
            # gate failure, not evidence of fail-stop.
            passed = (not timedout and code in (-6, 134)
                      and "FAIL" not in stdout)
        else:
            passed = not timedout and code == 0 and "PASS unsafe-preflight-quarantine" in stdout
        results["cases"].append({"build":name,"case":"unsafe-preflight",
                                 "exitCode":code,"timedOut":timedout,
                                 "passed":passed,"stdout":stdout,"stderr":stderr})
    # Negative test for the experiment gate: removing the fail-stop must be
    # rejected even though it exits nonzero and prints FAIL.
    mutant = out/"harness-mutant.c"
    mutdir = out/"mutant"
    mutdir.mkdir()
    src = (ex/"actual-vd.inc").read_text()
    mutated = src.replace("    abort();", "    return false;", 1)
    if mutated == src:
        results["cases"].append({"build":"mutant","case":"missing-abort",
                                 "passed":False,
                                 "error":"could not create missing-abort mutant"})
    else:
        (mutdir/"actual-vd.inc").write_text(mutated)
        mutant.write_text((out/"harness.c").read_text())
        cmd = ["clang","-std=c11","-D_POSIX_C_SOURCE=200809L","-DPHASE28",
               "-DMP_OHCODEC_LIFECYCLE_EXPERIMENT=1",
               "-Wall","-Wextra","-Werror","-Wno-unused-function",
               "-Wno-unused-parameter","-Wno-unused-but-set-variable","-g","-O0",
               "-I",str(out),"-I",str(mutdir),"-I",str(ex),str(mutant),"-o",str(out/"harness-mutant")]
        mc = subprocess.run(cmd,capture_output=True,text=True)
        (out/"compile-mutant.log").write_text(mc.stdout+mc.stderr)
        if mc.returncode:
            results["cases"].append({"build":"mutant","case":"missing-abort",
                                     "passed":False,"compileExit":mc.returncode})
        else:
            try:
                mp = subprocess.run([str(out/"harness-mutant"), "unsafe-preflight"],
                                    capture_output=True, text=True, timeout=5)
                code, stdout, stderr, timedout = mp.returncode, mp.stdout, mp.stderr, False
            except subprocess.TimeoutExpired as e:
                so = e.stdout or ""
                se = e.stderr or ""
                if isinstance(so, bytes): so = so.decode("utf-8", "replace")
                if isinstance(se, bytes): se = se.decode("utf-8", "replace")
                code, stdout, stderr, timedout = 124, so, se + "\nTIMEOUT", True
            (out/"run-mutant-unsafe.log").write_text(stdout+stderr)
            rejected = (not timedout and (code not in (-6, 134)
                                         or "FAIL" in stdout))
            results["cases"].append({"build":"mutant","case":"missing-abort",
                                     "exitCode":code,"timedOut":timedout,
                                     "passed":rejected,"stdout":stdout,
                                     "stderr":stderr,
                                     "note":"gate must reject a missing fail-stop"})
    # External watchdog bound: a deliberate hang must be terminated by the
    # host timeout, outside the diagnostic worker.
    binp = out/"harness-normal"
    try:
        p = subprocess.run([str(binp),"watchdog-hang"],capture_output=True,
                           text=True,timeout=2)
        wd = {"exitCode":p.returncode,"timedOut":False,"passed":False}
    except subprocess.TimeoutExpired:
        wd = {"exitCode":124,"timedOut":True,"passed":True,
              "note":"external host timeout terminated the hung diagnostic process"}
    results["cases"].append({"build":"normal","case":"watchdog-hang",**wd})
    ok = all(c.get("passed", False) for c in results["cases"])
    results["accepted"] = ok
    (out/"results.json").write_text(json.dumps(results,indent=2)+"\n")
    print("ACCEPTED" if ok else "NOT ACCEPTED")
    for c in results["cases"]:
        print(c.get("build"),c.get("case"),c.get("passed"),c.get("exitCode"),c.get("timedOut"))
    raise SystemExit(0 if ok else 1)
if __name__=="__main__": main()
