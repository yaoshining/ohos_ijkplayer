from pathlib import Path
import json,subprocess,zipfile,hashlib,shlex,difflib,time
R=Path(__file__).resolve().parents[1];run=R/'native-tests/run-01';env=json.loads((run/'commands.json').read_text())[0]['environment'];fixtures=R/'native-tests/fixtures';results=[]
def invoke(name,cmd,cwd,extra=None):
 log=fixtures/(name+'.log');start=time.time()
 with log.open('w') as f:p=subprocess.run(list(map(str,cmd)),cwd=cwd,env={**env,**(extra or {})},stdout=f,stderr=subprocess.STDOUT)
 results.append({'name':name,'command':list(map(str,cmd)),'cwd':str(cwd),'extraEnv':extra,'returncode':p.returncode,'log':str(log),'elapsedSeconds':time.time()-start});(fixtures/'repair-results.json').write_text(json.dumps(results,indent=2)+'\n');print(name,p.returncode,flush=True)
 if p.returncode:raise RuntimeError(name)
z=fixtures/'As.I.Lay.Dying.zip'
with zipfile.ZipFile(z) as f:data=f.read('As I Lay Dying.ttf')
assert hashlib.sha256(data).hexdigest().startswith('ef146bbc2673b387');(fixtures/'As.I.Lay.Dying.ttf').write_bytes(data)
(fixtures/'font-lock.json').write_text(json.dumps({'url':'https://github.com/python-pillow/Pillow/files/6622147/As.I.Lay.Dying.zip','archiveSHA256':hashlib.sha256(z.read_bytes()).hexdigest(),'fontSHA256':hashlib.sha256(data).hexdigest(),'upstreamExpectedDigestPrefix':'ef146bbc2673b387'},indent=2)+'\n')
invoke('freetype-issue1063',[run/'build/freetype/tests/issue-1063'],fixtures,{'FREETYPE_TESTS_DATA_DIR':str(fixtures)})
ninja='/Applications/DevEco-Studio.app/Contents/sdk/default/openharmony/native/build-tools/cmake/bin/ninja'
invoke('libass-checkasm-build',[ninja,'-C',run/'build/libass','-v','checkasm/checkasm'],run)
invoke('libass-checkasm',[run/'build/libass/checkasm/checkasm'],fixtures)
b=run/'build/fontconfig';db=json.loads((b/'compile_commands.json').read_text())
for name in ['issue110','d1f48f11']:
 src=run/'source/fontconfig/test'/('test-'+name+'.c');new=fixtures/src.name;old=src.read_text();text=old.replace('"/tmp/','"'+str(run/'tmp')+'/');assert text!=old;new.write_text(text);(fixtures/(name+'.patch')).write_text(''.join(difflib.unified_diff(old.splitlines(True),text.splitlines(True),'a/'+src.name,'b/'+src.name)))
 row=next(c for c in db if Path(c['file']).name==src.name);cmd=shlex.split(row['command']);output=Path(cmd[cmd.index('-o')+1]);obj=fixtures/(name+'.o');cmd[cmd.index('-o')+1]=str(obj);cmd[cmd.index('-c')+1]=str(new);cmd+=['-I'+str(src.parent)];invoke(name+'-compile',cmd,b)
 target='test/test_'+name;commands=subprocess.check_output([ninja,'-C',str(b),'-t','commands',target],text=True,env=env);line=next(x for x in commands.splitlines() if ' -o '+target+' ' in x);link=shlex.split(line);link[link.index('-o')+1]=str(fixtures/target.split('/')[-1]);link=[str(obj) if x==str(output) else x for x in link];invoke(name+'-link',link,b);invoke(name+'-test',[fixtures/target.split('/')[-1]],fixtures)
