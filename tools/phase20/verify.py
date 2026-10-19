"""Read actual target ELFs and link a target caller; do not execute target code."""
from pathlib import Path
import argparse,json,subprocess,importlib.util,os,re
import build
HERE=Path(__file__).resolve().parent
s=importlib.util.spec_from_file_location('elf',HERE/'recipe/elf-audit.py');elf=importlib.util.module_from_spec(s);s.loader.exec_module(elf)
def main():
 p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);p.add_argument('--ndk',type=Path,required=True);a=p.parse_args();out=a.out.resolve();ndk=a.ndk.resolve();readelf=ndk/'llvm/bin/llvm-readelf'
 baseline=json.loads((HERE/'baseline-exports.json').read_text())['libraries'];results=[]
 assert set(baseline)==build.EXPECTED_LIBRARIES
 for label in ['origin-a','longer-absolute-directory-b']:
  root=out/label;prefix=root/'ffmpeg/prefix';libs=build.collect_libraries(prefix/'lib',readelf);rows={}
  for name,digest in libs.items():
   lib=prefix/'lib'/name;inv=elf.inventory(lib.read_bytes());exports={x['name']:{k:x[k] for k in ['bind','type','visibility']} for x in inv['symbols'] if x['table']=='.dynsym' and x['sectionIndex'] and x['bind'] in (1,2)}
   old=baseline[name]['exports'];added=set(exports)-set(old);assert added==({'ohcodec_smb_runtime_configure_v1'} if name=='libavformat.so.62' else set()),(name,added)
   assert set(old)<=set(exports) and all(exports[n]==old[n] for n in old),name
   dump=subprocess.check_output([str(readelf),'--wide','-d','--dyn-syms','--version-info',str(lib)],text=True);(root/(name+'.elf.txt')).write_text(dump)
   versions=dict(re.findall(r'\b([\w.]+)@@?([A-Za-z0-9_]+)',dump));assert {n:versions.get(n) for n in old}==baseline[name]['exportVersions'],name+' old version mismatch'
   if name=='libavformat.so.62':assert 'ohcodec_smb_runtime_configure_v1@@LIBAVFORMAT_62' in dump
   rows[name]={'sha256':digest,'oldExportsPreserved':True,'newExports':sorted(added),'exportCount':len(exports)}
  cfg=(root/'ffmpeg/build/config.h').read_text()
  for macro in ['CONFIG_GNUTLS','CONFIG_LIBSMBCLIENT','CONFIG_OHCODEC']:assert '#define '+macro+' 1' in cfg,macro
  obj=list((root/'dependencies/work/samba/bin/default').rglob('dynconfig.c.*.o'));assert len(obj)==1
  raw=obj[0].read_bytes();assert b'/usr/local/samba/lib/python3/site-packages' in raw
  assert str(root).encode() not in raw,'build path leaked into dynconfig object'
  archive=root/'dependencies/sysroot/lib/libsmbclient.a';symbols=subprocess.check_output([str(ndk/'llvm/bin/llvm-nm'),'--defined-only',str(archive)],text=True);(root/'samba-defined-symbols.txt').write_text(symbols)
  for sym in ['ohcodec_smb_runtime_configure_internal','smbc_new_context','smbc_init_context','smbc_free_context']:assert sym in symbols
  bindings=json.loads((root/'ffmpeg/build/input-bindings.json').read_text());assert next(x for x in bindings['inputs'] if x['role']=='deps')['resolvedPath']==str(root/'dependencies/sysroot')
  client=root/'api-caller.c';client.write_text('#include <libavformat/ohcodec_smb_runtime.h>\nint configure(const struct ohcodec_smb_runtime_v1 *p) { return ohcodec_smb_runtime_configure_v1(p); }\n')
  args=[str(ndk/'llvm/bin/aarch64-unknown-linux-ohos-clang'),'-fPIC','-shared',str(client),'-I'+str(prefix/'include'),'-L'+str(prefix/'lib'),'-Wl,-rpath-link,'+str(prefix/'lib'),'-Wl,--no-undefined','-lavformat','-o',str(root/'api-caller.so')]
  with (root/'api-caller-link.log').open('w') as f:subprocess.run(args,stdout=f,stderr=subprocess.STDOUT,check=True)
  build.write(root/'api-caller-link.json',{'argv':args,'callerSHA256':build.sha(root/'api-caller.so'),'targetExecuted':False})
  results.append({'run':label,'libraries':rows,'dynconfigObjectSHA256':build.sha(obj[0]),'staticSambaSHA256':build.sha(archive),'pythonTargetPathPreserved':True,'actualDependencyBinding':bindings,'callerLinked':True})
 build.write(out/'verification.json',{'runs':results,'formalArtifactAllowed':False,'targetExecuted':False,'deviceAcceptanceStatus':'pending'})
if __name__=='__main__':main()
