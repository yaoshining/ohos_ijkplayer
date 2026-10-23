from pathlib import Path
import tempfile,shutil,json
import analyze as m
base=m.R;rows=[]
with tempfile.TemporaryDirectory(prefix='phase29-device-gate-') as folder:
 r=Path(folder);(r/'evidence').mkdir();shutil.copytree(base/'artifacts',r/'artifacts',ignore=shutil.ignore_patterns('*.hap'));name='device-ui-fatal-03';shutil.copytree(base/'evidence'/name,r/'evidence'/name);m.R=r;d=r/'evidence'/name
 originals={p:p.read_bytes() for p in d.iterdir() if p.is_file()}
 def run(label,mutate,want):
  for p,b in originals.items():p.write_bytes(b)
  mutate();v=m.analyze(name,'fault-ui2.json','ui');rows.append({'case':label,'actualAccepted':v['passed'],'expectedAccepted':want,'passed':v['passed']==want,'failedChecks':[k for k,x in v['checks'].items() if not x]})
 def pre(mut):
  p=d/'before-cleanup.json';x=json.loads(p.read_text());mut(x);p.write_text(json.dumps(x))
 run('valid',lambda:None,True)
 run('residual-window',lambda:pre(lambda x:x['window'].update(stdout=x['window']['stdout']+'\nphase22probe0 6214\n')),False)
 run('query-timeout',lambda:pre(lambda x:x['window'].update(exit=124,timeout=15,stdout='')),False)
 run('targets-timeout-with-stale-output',lambda:pre(lambda x:x['targets'].update(exit=124,timeout=15)),False)
 run('offline',lambda:pre(lambda x:x['targets'].update(stdout=x['targets']['stdout'].replace('Connected','Offline'))),False)
 def replace(n,a,b):p=d/n;p.write_text(p.read_text(errors='replace').replace(a,b))
 run('wrong-system-pid',lambda:replace('system-live.log','with pid 6214 exit','with pid 99999 exit'),False)
 run('wrong-system-exit',lambda:replace('system-live.log','exit with code:0','exit with code:86'),False)
 run('missing-ui2',lambda:replace('terminal-events.log','event=ui code=2','event=ui code=12'),False)
 run('missing-library-identity',lambda:replace('vk-inject-wait-0.log','mapped_expected_libraries=7 all_sha_match=1','mapped_expected_libraries=0 all_sha_match=0'),False)
print(json.dumps({'cases':rows,'accepted':all(x['passed'] for x in rows)},indent=2));raise SystemExit(0 if all(x['passed'] for x in rows) else 1)
