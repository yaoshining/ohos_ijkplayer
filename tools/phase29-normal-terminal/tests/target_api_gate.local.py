from pathlib import Path
import subprocess,json,hashlib
R=Path(__file__).resolve().parent.parent;out=R/'evidence/target-api-04';out.mkdir(exist_ok=False);sdk=Path('/Applications/DevEco-Studio.app/Contents/sdk/default/openharmony/native');llvm=sdk/'llvm/bin';expected={'mpv_ohcodec_terminal_api_version','mpv_ohcodec_terminal_register','mpv_ohcodec_terminal_enable','mpv_ohcodec_terminal_snapshot'}
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
commands=[]
def command(name,args):
 p=subprocess.run([str(a) for a in args],capture_output=True,text=True,timeout=30);(out/(name+'.log')).write_text(p.stdout+p.stderr);commands.append({'name':name,'argv':[str(a) for a in args],'exit':p.returncode});(out/'commands.json').write_text(json.dumps(commands,indent=2));return p
rows=[]
for name in ['normal-e','normal-f']:
 b=R/'build'/name;lib=b/'install/usr/local/lib/libmpv.so';nm=command(name+'-symbols',[llvm/'llvm-nm','-D','--defined-only',lib]);assert nm.returncode==0
 exported={l.split()[-1] for l in nm.stdout.splitlines() if l.split()};public={x for x in exported if x.startswith('mpv_')};assert expected<=public and len(public)==58 and not any(x.startswith('mp_ohcodec_terminal_') for x in exported)
 compdb=json.loads((b/'mpv/build/compile_commands.json').read_text());wrapper=[x for x in compdb if x['file'].endswith('/ohcodec_terminal_api.c')];assert len(wrapper)==1
 bind={}
 for rel in ['meson.build','video/out/hwdec/ohcodec_terminal_api.c','video/out/hwdec/ohcodec_terminal.c','include/mpv/ohcodec_terminal.h']:
  assert sha(b/'mpv/source'/rel)==sha(R/'input-package/sources/mpv'/rel);bind[rel]=sha(b/'mpv/source'/rel)
 installed=b/'install/usr/local/include/mpv/ohcodec_terminal.h';assert sha(installed)==bind['include/mpv/ohcodec_terminal.h']
 assert not any('-DMP_OHCODEC_DIAGNOSTIC' in x['command'] or '-DMP_OHCODEC_LIFECYCLE_EXPERIMENT' in x['command'] for x in compdb)
 links=[]
 for lang,compiler in [('c','clang'),('c++','clang++')]:
  output=out/(name+'-'+compiler);args=[llvm/compiler,'--target=aarch64-linux-ohos','--sysroot='+str(sdk/'sysroot'),'-I'+str(b/'install/usr/local/include'),'-x',lang,R/'tests/abi_target.c','-x','none',lib,'-Wl,--no-undefined','-Wl,-rpath-link,'+str(b/'mpv/source/_staged/ffmpeg/lib'),'-o',output]
  p=command(name+'-'+compiler,args);links.append({'language':lang,'exit':p.returncode,'sha256':sha(output) if output.exists() else None});assert p.returncode==0
 rows.append({'build':name,'mpvSHA256':sha(lib),'sourceBinding':bind,'wrapperCommand':wrapper[0],'publicCount':len(public),'extension':sorted(expected),'internalExported':False,'installedHeaderSHA256':sha(installed),'targetLinks':links,'linkNoUndefined':True,'allFourReferenced':True})
assert rows[0]['mpvSHA256']==rows[1]['mpvSHA256']
(out/'results.json').write_text(json.dumps({'accepted':True,'twoCleanEqual':True,'runtimeExecuted':False,'builds':rows},indent=2));print(json.dumps({'accepted':True,'sha256':rows[0]['mpvSHA256']}))
