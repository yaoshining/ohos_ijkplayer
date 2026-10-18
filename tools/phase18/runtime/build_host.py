"""Build native dependency group from fixed source package in a new root."""
from pathlib import Path
import argparse,json,os,shutil,subprocess,sys,time
from input_gate import sha,inventory,verify_tree,require_fresh
R=Path(__file__).resolve().parents[1];ap=argparse.ArgumentParser();ap.add_argument('--run',required=True,type=Path);ap.add_argument('--jobs',default=8,type=int);a=ap.parse_args()
P=R/'source-package';verify_tree(P/'source',json.loads((P/'source-final.json').read_text()),source=True)
tools=json.loads((R/'locks/tools-before.json').read_text());S=Path(tools['SDK']);LLVM=S/'llvm/bin';MESON=Path('/Users/yaoshining/anaconda3/bin/meson');NINJA=S/'build-tools/cmake/bin/ninja';PKG=Path('/opt/homebrew/bin/pkg-config')
for row in tools['tools']:
 if sha(row['path'])!=row['sha256']:raise ValueError('tool input drift: '+row['path'])
RUN=require_fresh(a.run);RUN.mkdir(parents=True);PREFIX=RUN/'prefix'
for n in ['logs','home','tmp','cache','build','build-tools','prefix/lib/pkgconfig','prefix/include']:(RUN/n).mkdir(parents=True,exist_ok=True)
shutil.copytree(P/'source',RUN/'source');verify_tree(RUN/'source',json.loads((P/'source-final.json').read_text()),source=True)
flags=['-isysroot',tools['nativeSDK'],'-fPIC','-fmacro-prefix-map='+str(RUN)+'=.']
link=['-isysroot',tools['nativeSDK']]
text="[host_machine]\nsystem='linux'\ncpu_family='aarch64'\ncpu='arm64-v8a'\nendian='little'\n[properties]\nneeds_exe_wrapper=true\n[binaries]\n"
for k,v in {'c':Path(tools['nativeClang']),'cpp':Path(tools['nativeClang']).parent/'clang++','ar':LLVM/'llvm-ar','strip':LLVM/'llvm-strip','c_ld':LLVM/'ld.lld','cpp_ld':LLVM/'ld.lld','pkg-config':PKG}.items():text+=k+'='+repr(str(v))+'\n'
text+='[built-in options]\n'
for k,v in {'c_args':flags,'cpp_args':flags,'c_link_args':link,'cpp_link_args':link}.items():text+=k+'='+repr(v)+'\n'
CROSS=RUN/'build-tools/target.ini';CROSS.write_text(text)
text='[binaries]\n'
for k,v in {'c':tools['nativeClang'],'cpp':str(Path(tools['nativeClang']).parent/'clang++'),'ar':str(LLVM/'llvm-ar'),'strip':str(Path(tools['nativeClang']).parent/'strip'),'pkg-config':str(PKG),'python':sys.executable,'python3':sys.executable,'gperf':'/usr/bin/gperf'}.items():text+=k+'='+repr(v)+'\n'
text+='[built-in options]\n'
for k in ['c_args','cpp_args','c_link_args','cpp_link_args']:text+=k+'='+repr(['-isysroot',tools['nativeSDK']])+'\n'
NATIVE=RUN/'build-tools/native.ini';NATIVE.write_text(text)
env={'PATH':':'.join([str(NINJA.parent),str(MESON.parent),str(LLVM),'/usr/bin','/bin','/usr/sbin','/sbin']),'HOME':str(RUN/'home'),'TMPDIR':str(RUN/'tmp'),'XDG_CACHE_HOME':str(RUN/'cache'),'MESON_PACKAGE_CACHE_DIR':str(RUN/'cache/meson'),'LANG':'C','LC_ALL':'C','TZ':'UTC','SOURCE_DATE_EPOCH':'1760000000','PYTHONDONTWRITEBYTECODE':'1','PYTHONNOUSERSITE':'1','GIT_OPTIONAL_LOCKS':'0','GIT_CONFIG_NOSYSTEM':'1','GIT_CONFIG_GLOBAL':os.devnull,'GIT_CEILING_DIRECTORIES':str(RUN),'PKG_CONFIG':str(PKG),'PKG_CONFIG_PATH':str(PREFIX/'lib/pkgconfig'),'PKG_CONFIG_LIBDIR':str(PREFIX/'lib/pkgconfig'),'CCACHE_DISABLE':'1','NINJA_STATUS':'[%f/%t] '}
commands=[]
def run(name,argv,cwd=RUN,extra=None):
 e={**env,**(extra or {})};log=RUN/'logs'/(name+'.log');start=time.time()
 with log.open('w') as stream:pr=subprocess.run(list(map(str,argv)),cwd=cwd,env=e,stdout=stream,stderr=subprocess.STDOUT)
 row={'name':name,'argv':list(map(str,argv)),'cwd':str(cwd),'environment':e,'returncode':pr.returncode,'elapsedSeconds':time.time()-start,'log':str(log.relative_to(RUN))};commands.append(row);(RUN/'commands.json').write_text(json.dumps(commands,indent=2)+'\n');print(name,pr.returncode,flush=True)
 if pr.returncode:raise RuntimeError('Failed '+str(log))
installs=[]
def copyinstall(src,dest):
 dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(src,dest);before=sha(dest)
 if dest.suffix=='.pc':
  t=dest.read_text();t=t.replace('prefix=/usr/local','prefix=${pcfiledir}/../..');dest.write_text(t)
 installs.append({'source':str(src),'destination':str(dest),'sourceSHA256':sha(src),'installedSHA256':sha(dest),'pcRelocated':before!=sha(dest)})
recipe=json.loads((R/'research/native/recipe.json').read_text());replacements={'<RUN>':str(RUN),'<MESON>':str(MESON),'<NINJA>':str(NINJA),'<CROSS>':str(CROSS),'<NATIVE>':str(NATIVE)}
def argv(raw):
 out=[]
 for v in raw:
  for k,b in replacements.items():v=v.replace(k,b)
  out.append(v)
 return out
(RUN/'input-binding.json').write_text(json.dumps({'sourceLockSHA256':sha(R/'locks/source-lock.json'),'toolLockSHA256':sha(R/'locks/tools-before.json'),'recipeSHA256':sha(R/'research/native/recipe.json'),'scriptSHA256':sha(__file__),'freshRoot':True,'targetCodeExecuted':False,'hostTestBuild':True},indent=2)+'\n')
for c in recipe['components']:
 name=c['component'];build=RUN/'build'/name
 if 'setupArgv' in c:
  items=c['setupArgv'];i=items.index('--cross-file');del items[i:i+2]
  tests={'fribidi':('-Dtests=false','-Dtests=true'),'lcms2':('-Dtests=disabled','-Dtests=enabled'),'freetype':('-Dtests=disabled','-Dtests=enabled'),'fontconfig':('-Dtests=disabled','-Dtests=enabled'),'libass':('-Dcheckasm=disabled','-Dcheckasm=enabled')}
  if name in tests:
   old,new=tests[name];c['setupArgv']=[new if v==old else v for v in items]
 if name=='lua':
  shutil.copytree(RUN/'source/lua',build)
  run('lua-build',['/usr/bin/make','-C',build/'src','macosx','CC='+tools['nativeClang']+' -isysroot '+tools['nativeSDK'],'AR='+str(LLVM/'llvm-ar')+' rcu','RANLIB='+str(LLVM/'llvm-ranlib'),'MYCFLAGS=-fPIC -fmacro-prefix-map='+str(RUN)+'=.','LUA_T=lua','LUAC_T=luac','-j'+str(a.jobs)])
  copyinstall(build/'src/liblua.a',PREFIX/'lib/liblua.a')
  for n in c['installPlan']['headers']:copyinstall(RUN/'source/lua/src'/n,PREFIX/'include'/n)
  (PREFIX/'lib/pkgconfig/lua.pc').write_text(c['installPlan']['pcText'].replace('<RUN>/prefix','${pcfiledir}/../..'))
 else:
  run(name+'-setup',argv(c['setupArgv']));run(name+'-build',argv(c['buildArgv'])+['-j'+str(a.jobs)])
  run(name+'-deps',[NINJA,'-C',build,'-t','deps']);run(name+'-commands',[NINJA,'-C',build,'-t','commands'])
  before={x['path']:x for x in inventory(PREFIX)};run(name+'-install',argv(c['installArgv']))
  # Every install comes from this run's DESTDIR; accumulated files are source-bound individually.
  dest=RUN/'destdir/usr/local'
  for sub in ['lib','include']:
   for p in sorted((dest/sub).rglob('*')):
    if p.is_file():copyinstall(p,PREFIX/p.relative_to(dest))
 (RUN/'install-binding.json').write_text(json.dumps(installs,indent=2)+'\n')
 (RUN/'prefix-files.json').write_text(json.dumps(inventory(PREFIX),indent=2)+'\n')
verify_tree(RUN/'source',json.loads((P/'source-final.json').read_text()),source=True)
print('Host component build complete:',RUN,flush=True)
