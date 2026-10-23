from pathlib import Path
import json,subprocess,time
R=Path(__file__).resolve().parents[1];run=R/'native-tests/run-01';env=json.loads((run/'commands.json').read_text())[0]['environment'];env.update({'FONTCONFIG_FILE':str(run/'destdir/usr/local/etc/fonts/fonts.conf'),'FONTCONFIG_PATH':str(run/'destdir/usr/local/etc/fonts'),'XDG_CACHE_HOME':str(run/'cache')});results=[]
select={'fribidi':[],'lcms2':[],'xml2':['testparser','testdict','testchar','testrecurse','runtest'],'freetype':[],'fontconfig':['test_name_parse','test_family_matching','test_ptrlist','test_issue110','test_d1f48f11'],'libass':[]}
for component,names in select.items():
 argv=['/Users/yaoshining/anaconda3/bin/meson','test','-C',str(run/'build'/component),'--no-rebuild','--print-errorlogs','--timeout-multiplier','2',*names];log=run/'logs'/(component+'-tests.log');start=time.time()
 with log.open('w') as f:p=subprocess.run(argv,env=env,cwd=run,stdout=f,stderr=subprocess.STDOUT)
 result={'component':component,'argv':argv,'environment':env,'returncode':p.returncode,'elapsedSeconds':time.time()-start,'log':str(log)};results.append(result);(run/'test-results.json').write_text(json.dumps(results,indent=2)+'\n');print(component,p.returncode,flush=True)
print('Host test suite commands complete',flush=True)
