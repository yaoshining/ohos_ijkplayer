"""两个全新目标根编译链接；不执行目标代码，不改变任何既有库。"""
from pathlib import Path
import argparse,json,shutil,subprocess,re
from common import *
from resources import prepare

def resolve_library(root,soname,digest):
 candidates={p.resolve() for p in Path(root).glob(soname+'*') if p.is_file() and (p.name==soname or p.name.startswith(soname+'.'))}
 if len(candidates)!=1:raise ValueError('missing or ambiguous target library: '+soname)
 result=next(iter(candidates));require(result,digest);return result

def main():
 p=argparse.ArgumentParser()
 for n in ['out','ndk','ffmpeg','headers','mpv-prefix','placebo']:p.add_argument('--'+n,type=Path,required=True)
 p.add_argument('--profile',choices=['macOS','Linux'],required=True);a=p.parse_args()
 for n in ['out','ndk','ffmpeg','headers','mpv_prefix','placebo']:setattr(a,n,getattr(a,n).resolve())
 a.out.mkdir(parents=True,exist_ok=False);lock=json.loads((HERE/'binding-lock.json').read_text());expected=lock[a.profile]
 libs={name:resolve_library(a.ffmpeg,name,digest) for name,digest in expected['ffmpeg'].items()};libs['libmpv.so']=a.mpv_prefix/'lib/libmpv.so'
 for n,f in libs.items():require(f,expected['mpv'] if n=='libmpv.so' else expected['ffmpeg'][n])
 require(a.placebo,expected['libplacebo']);headers={a.headers/n:h for n,h in lock['headers'].items() if n!='libavformat/ohcodec_smb_runtime.h'}
 headers.update({a.mpv_prefix/'include/mpv'/n:h for n,h in lock['mpvHeaders'].items()})
 runtime=HERE.parent/'phase20/runtime/smb_runtime.h';require(runtime,lock['headers']['libavformat/ohcodec_smb_runtime.h'])
 for f,h in headers.items():require(f,h)
 before=[pin(f) for f in list(libs.values())+list(headers)+[runtime,a.placebo]+list(HERE.glob('*.c'))+list(HERE.glob('*.h'))]
 clang=a.ndk/'llvm/bin/clang';readelf=a.ndk/'llvm/bin/llvm-readelf';write(a.out/'inputs-before.json',{'files':before,'tools':[pin(a.ndk/'llvm/bin'/n) for n in ['clang','ld.lld','llvm-readelf']],'profile':a.profile,'staticPlaceboInsideMpv':True})
 results=[]
 for label in ['origin-a','longer-absolute-directory-b']:
  r=a.out/label;r.mkdir();(r/'lib').mkdir();(r/'include/libavformat').mkdir(parents=True)
  for name,f in libs.items():shutil.copyfile(f,r/'lib'/name)
  shutil.copyfile(runtime,r/'include/libavformat/ohcodec_smb_runtime.h')
  for name in ['integration.c','integration.h','preflight.c','probe.c']:shutil.copyfile(HERE/name,r/name)
  args=[clang,'--target=aarch64-linux-ohos','--sysroot='+str(a.ndk/'sysroot'),'-std=c11','-O2','-fPIE','-pie','-pthread','-D__MUSL__=1','-Iinclude','-I'+str(a.headers),'-I'+str(a.mpv_prefix/'include'),'integration.c','preflight.c','probe.c','-Wl,--no-undefined','-Wl,--no-allow-shlib-undefined','-Wl,--no-as-needed','-Wl,-rpath,$ORIGIN/lib','-Wl,-rpath-link,lib','-Wl,-rpath-link,'+str(a.ndk/'sysroot/usr/lib/aarch64-linux-ohos'),'-Wl,-Map,link.map','-Wl,--trace']+['lib/'+n for n in libs]+['-o','phase21-probe']
  run(args,r/'link.log',r)
  dump=run([readelf,'--wide','-h','-d','--dyn-syms','--version-info','phase21-probe'],r/'probe-elf.txt',r)
  assert 'AArch64' in dump and 'ohcodec_smb_runtime_configure_v1@LIBAVFORMAT_62' in dump
  needed=re.findall(r'Shared library: \[(.*?)\]',dump);assert set(libs)<=set(needed),(needed,list(libs))
  assert '$ORIGIN/lib' in dump
  mpvdump=run([readelf,'--wide','--dyn-syms','lib/libmpv.so'],r/'mpv-symbols.txt',r)
  imports=set(re.findall(r'\b(\w+)@(LIB(?:AV\w+|SW\w+)_\d+)',mpvdump));exports=set()
  for n in libs:
   if n=='libmpv.so':continue
   t=run([readelf,'--wide','-d','--dyn-syms','lib/'+n],r/(n+'.symbols.txt'),r);assert 'Library soname: ['+n+']' in t;exports.update(re.findall(r'\b(\w+)@@(LIB(?:AV\w+|SW\w+)_\d+)',t))
  assert len(imports)==247 and imports<=exports,(len(imports),imports-exports)
  link=(r/'link.log').read_text();assert all('lib/'+n in link for n in libs)
  prepare(r/'runtime-example')
  results.append({'root':label,'probe':pin(r/'phase21-probe'),'libraries':{n:sha(r/'lib'/n) for n in libs},'needed':needed,'versionedMpvImports':len(imports),'missingImports':[],'targetExecuted':False})
 for f in before:require(f['path'],f['sha256'])
 assert results[0]['probe']['sha256']==results[1]['probe']['sha256'],'cross-root probe bytes differ'
 write(a.out/'verification.json',{'runs':results,'crossRootProbeBytesEqual':True,'inputsUnchanged':True,'targetExecuted':False,'deviceAcceptanceStatus':'pending','formalArtifactAllowed':False})
if __name__=='__main__':main()
