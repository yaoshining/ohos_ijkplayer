import os,sys,subprocess,json,hashlib,shutil
from pathlib import Path
p=Path(__file__).resolve().parent
stage=sys.argv[1];out=p/stage;out.mkdir(exist_ok=False)
subprocess.run([sys.executable,'-B',str(p/'extract.py')],check=True)
for n in ['harness.c','actual-functions.inc','source-binding.json']:shutil.copy2(p/n,out/n)
cmd=['clang','-std=c11','-Wall','-Wextra','-Werror','-Wno-unused-function','-fsanitize=address,undefined','-g',str(out/'harness.c'),'-o',str(out/'harness')]
r=subprocess.run(cmd,capture_output=True,text=True);(out/'compile.log').write_text(r.stdout+r.stderr)
if r.returncode:raise SystemExit(r.returncode)
rows=[]
for name in ['first-failure','transition-failure','invalidate-failure','stale-current','target-limited','sdr-output','matching-control','cache','retry','invalidate','transitions']+['field-'+str(i) for i in range(12)]:
 r=subprocess.run([str(out/'harness'),name],capture_output=True,text=True,env=dict(os.environ,ASAN_OPTIONS='halt_on_error=1:detect_leaks='+('0' if sys.platform=='darwin' else '1'),UBSAN_OPTIONS='halt_on_error=1:print_stacktrace=1'))
 rows.append(dict(case=name,exitCode=r.returncode,stdout=r.stdout,stderr=r.stderr));(out/(name+'.log')).write_text(r.stdout+r.stderr)
(out/'results.json').write_text(json.dumps(dict(cases=rows,compileCommand=cmd),indent=2)+'\n')
print(json.dumps({'stage':stage,'passed':sum(r['exitCode']==0 for r in rows),'failed':[r['case']for r in rows if r['exitCode']]}))
raise SystemExit(any(r['exitCode']for r in rows))
