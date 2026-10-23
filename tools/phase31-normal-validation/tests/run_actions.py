from pathlib import Path
import subprocess,json,hashlib,argparse,shutil
p=argparse.ArgumentParser();p.add_argument('--out',required=True,type=Path);p.add_argument('--header',type=Path);a=p.parse_args();root=Path(__file__).resolve().parents[1];out=a.out;out.mkdir(exist_ok=False,parents=True)
h=a.header or root/'app/entry/src/main/cpp/phase31_actions.h';shutil.copyfile(h,out/'phase31_actions.h');shutil.copyfile(root/'tests/actions.cpp',out/'actions.cpp')
cmd=['clang++','-std=c++17','-I'+str(out),'-I'+str(root/'app/entry/src/main/cpp'),str(out/'actions.cpp'),'-o',str(out/'test')];c=subprocess.run(cmd,capture_output=True,text=True);(out/'compile.log').write_text(c.stdout+c.stderr);run=None
if c.returncode==0:
 run=subprocess.run([str(out/'test')],capture_output=True,text=True,timeout=10);(out/'run.log').write_text(run.stdout+run.stderr)
d={'compileExit':c.returncode,'runExit':run.returncode if run else None,'accepted':c.returncode==0 and run.returncode==0,'headerSHA256':hashlib.sha256(h.read_bytes()).hexdigest(),'testSHA256':hashlib.sha256((out/'actions.cpp').read_bytes()).hexdigest(),'cases':13};(out/'results.json').write_text(json.dumps(d,indent=2)+'\n');print(json.dumps(d));raise SystemExit(not d['accepted'])
