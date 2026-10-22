import subprocess,json,sys,os,shutil,argparse
from pathlib import Path
R=Path(__file__).resolve().parent.parent;p=argparse.ArgumentParser();p.add_argument('--phase',choices=['red','green'],required=True);p.add_argument('--suffix',default='');p.add_argument('--out',type=Path);a=p.parse_args();out=a.out or R/'evidence'/('abi-'+a.phase+a.suffix);out.mkdir(exist_ok=False)
src=R/'input-package/sources/mpv';mgr=src/'video/out/hwdec';inc=out/'include/mpv';inc.mkdir(parents=True);shutil.copy2(R/'api-contract/ohcodec_terminal.h',inc);shutil.copy2(src/'include/mpv/client.h',inc)
def run(label,args):
 try:
  p=subprocess.run(args,capture_output=True,text=True,timeout=15);text=p.stdout+p.stderr;rc=p.returncode
 except subprocess.TimeoutExpired as e:
  norm=lambda v:v.decode(errors='replace') if isinstance(v,bytes) else v or ''
  text=norm(e.stdout)+norm(e.stderr)+'\nTIMEOUT';rc=124
 (out/(label+'.log')).write_text(text);return rc
cc=['clang','-std=c11','-D_POSIX_C_SOURCE=200809L','-fvisibility=hidden','-fsanitize=address,undefined','-I'+str(out/'include'),'-I'+str(mgr),'-pthread','-fPIC'];lib=out/('libterminal.dylib' if sys.platform=='darwin' else 'libterminal.so')
assert run('manager',cc+['-Dpthread_create=probe_thread_create','-c',str(mgr/'ohcodec_terminal.c'),'-o',str(out/'manager.o')])==0
args=cc+(['-dynamiclib'] if sys.platform=='darwin' else ['-shared'])+[str(out/'manager.o'),str(R/'tests/abi_hooks.c'),'-o',str(lib)]
if a.phase=='green':args+=[str(mgr/'ohcodec_terminal_api.c')]
assert run('shared',args)==0
assert run('compile-probe',cc+[str(R/'tests/abi_probe.c'),'-ldl','-o',str(out/'probe')])==0
rows=[]
for c in ['invalid','retry','future-copy']:
 rc=run(c,[str(out/'probe'),str(lib),c]);rows.append({'case':c,'exit':rc,'expected':3 if a.phase=='red' else 0,'passed':rc==(3 if a.phase=='red' else 0)})
if a.phase=='green':
 for lang,name in [('clang++','cpp'),('clang','c')]:
  args=[lang,'-fsanitize=address,undefined','-I'+str(out/'include'),'-x','c++' if name=='cpp' else 'c',str(R/'tests/abi_link.cpp'),'-x','none',str(lib),'-o',str(out/name)];rc=run('link-'+name,args)
  rows.append({'case':'actual-dynamic-link-'+name,'exit':rc,'passed':rc==0 and run('exec-'+name,[str(out/name)])==0})
res={'phase':a.phase,'cases':rows,'accepted':all(x['passed'] for x in rows),'semanticMeaning':'missing exported API' if a.phase=='red' else 'host public contract only'};(out/'results.json').write_text(json.dumps(res,indent=2));print(json.dumps(res));sys.exit(0 if res['accepted'] else 1)
