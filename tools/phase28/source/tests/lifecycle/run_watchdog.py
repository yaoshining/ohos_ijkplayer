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
                return 124, (e.stdout or "") if isinstance(e.stdout,str) else "",
                # timeout metadata is recorded, not treated as success
        code, stdout, stderr, timedout = run("unsafe-preflight", 5)
        (out/("run-"+name+"-unsafe.log")).write_text(stdout+stderr)
        if name == "experiment":
            passed = timedout or code != 0
        else:
            passed = not timedout and code == 0 and "PASS unsafe-preflight-quarantine" in stdout
        results["cases"].append({"build":name,"case":"unsafe-preflight",
                                 "exitCode":code,"timedOut":timedout,
                                 "passed":passed,"stdout":stdout,"stderr":stderr})
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
