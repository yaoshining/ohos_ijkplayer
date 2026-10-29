"""Two fresh Samba/TLS -> FFmpeg diagnostic chains; no application writes."""
from pathlib import Path
import argparse,hashlib,json,os,platform,shutil,subprocess,sys,time,importlib.util,concurrent.futures,re
HERE=Path(__file__).resolve().parent;RECIPE=HERE/'recipe'
EXPECTED_LIBRARIES={'libavcodec.so.62','libavformat.so.62','libavutil.so.60','libavfilter.so.11','libswresample.so.6','libswscale.so.9'}
def collect_libraries(directory,readelf):
 files={p.name:p for p in Path(directory).glob('*.so.*') if p.is_file() and not p.is_symlink()}
 if len(files)!=len(EXPECTED_LIBRARIES):raise ValueError('incomplete/unexpected FFmpeg library set: '+repr(sorted(files)))
 result={}
 for name,p in sorted(files.items()):
  with p.open('rb') as f:header=f.read(20)
  if len(header)!=20 or header[:7]!=b'\x7fELF\x02\x01\x01' or header[16:20]!=b'\x03\x00\xb7\x00':raise ValueError('not an AArch64 shared ELF: '+str(p))
  dynamic=subprocess.check_output([str(readelf),'-d',str(p)],text=True)
  sonames=re.findall(r'\(SONAME\).*?\[([^\]]+)\]',dynamic)
  if len(sonames)!=1 or sonames[0] not in EXPECTED_LIBRARIES or sonames[0] in result:raise ValueError('unexpected/duplicate SONAME: '+str(p))
  soname=sonames[0]
  if name!=soname and not name.startswith(soname+'.'):raise ValueError('library name does not match SONAME: '+str(p))
  if not (Path(directory)/soname).is_file() or (Path(directory)/soname).resolve()!=p.resolve():raise ValueError('SONAME link does not resolve to library: '+str(p))
  result[soname]=sha(p)
 if set(result)!=EXPECTED_LIBRARIES:raise ValueError('incomplete FFmpeg SONAME set')
 return result
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
 return h.hexdigest()
def require_fresh(p):
 if Path(p).exists():raise ValueError('refuse existing output: '+str(p))
def require_sha(p,digest):
 if sha(p)!=digest:raise ValueError('source digest mismatch: '+str(p))
def write(p,d):Path(p).write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
def command(argv,log,env,cwd=None):
 started=time.time()
 with Path(log).open('w') as f:r=subprocess.run([str(x) for x in argv],cwd=cwd,env=env,stdout=f,stderr=subprocess.STDOUT)
 write(str(log)+'.json',{'argv':[str(x) for x in argv],'cwd':str(cwd or Path.cwd()),'exitCode':r.returncode,'elapsedSeconds':time.time()-started,'environment':env})
 if r.returncode:raise RuntimeError(str(log))
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--out',type=Path,required=True);ap.add_argument('--ndk',type=Path,required=True);ap.add_argument('--cache',type=Path,required=True);ap.add_argument('--ffmpeg-tar',type=Path,required=True);ap.add_argument('--jobs',default='6');ap.add_argument('--parallel',type=int,default=1);a=ap.parse_args()
 out=a.out.resolve();ndk=a.ndk.resolve();cache=a.cache.resolve();ff=a.ffmpeg_tar.resolve();require_fresh(out)
 source_lock=json.loads((RECIPE/'dependency-sources.lock.json').read_text())
 for row in source_lock['sources']:require_sha(cache/row['archiveFile'],row['sha256'])
 require_sha(ff,json.loads((RECIPE/'producer-inputs.lock.json').read_text())['ffmpeg']['gitArchiveSha256'])
 out.mkdir(parents=True)
 spec=importlib.util.spec_from_file_location('phase20_host_lock',RECIPE/'host-lock.py');host=importlib.util.module_from_spec(spec);spec.loader.exec_module(host)
 if platform.system()=='Darwin':os.environ['SDKROOT']=subprocess.check_output(['xcrun','--show-sdk-path'],text=True).strip()
 os.environ.update(PYTHONDONTWRITEBYTECODE='1',PYTHONNOUSERSITE='1',LC_ALL='C',TZ='UTC',PYTHONHASHSEED='1',SOURCE_DATE_EPOCH='1755820644')
 lock=host.capture(ndk,HERE,'phase20-'+platform.system());write(out/'host-lock.json',lock)
 sourcepins=[{'path':str(cache/r['archiveFile']),'sha256':r['sha256']}for r in source_lock['sources']]+[{'path':str(ff),'sha256':sha(ff)}];write(out/'source-pins.json',sourcepins)
 def build(label):
  root=out/label;root.mkdir();dep=root/'dependencies';dep.mkdir();home=root/'host-home';home.mkdir()
  env={k:os.environ[k] for k in ['PATH','TMPDIR','SDKROOT','DEVELOPER_DIR','TOOLCHAINS'] if k in os.environ}
  env.update(HOME=str(home),PYTHONDONTWRITEBYTECODE='1',PYTHONNOUSERSITE='1',LC_ALL='C',TZ='UTC',PYTHONHASHSEED='1',SOURCE_DATE_EPOCH='1755820644',OHOS_NDK=str(ndk),OHOS_SYSROOT=str(ndk/'sysroot'),OHOS_LLVM_BIN=str(ndk/'llvm/bin'),OHOS_ARCH='arm64-v8a',HOSTCC=str(Path(shutil.which('clang')).resolve()),M4=str(Path(shutil.which('m4')).resolve()),WORK_DIR=str(dep/'work'),PREFIX=str(dep/'sysroot'),SOURCE_CACHE=str(cache),JOBS=a.jobs,FFMPEG8_PIN_HOST_BISON='1',FFMPEG8_HOST_LOCK_SHA256=sha(out/'host-lock.json'))
  host.verify(lock);host.verify_binding(lock,ndk,HERE)
  command(['bash',RECIPE/'build-libsmbclient.sh'],root/'dependencies.log',env)
  command([sys.executable,'-B',RECIPE/'verify-dependency-features.py','--work',dep/'work','--sysroot',dep/'sysroot','--output',root/'dependency-features.json'],root/'dependency-features.log',env)
  env.update(SMB_PREFIX=str(dep/'sysroot'),PHASE20_FFMPEG_TAR=str(ff),FFMPEG_SOURCE_REPO='fixed-archive-no-git-discovery',OUTPUT_ROOT=str(root/'ffmpeg'))
  command(['bash',RECIPE/'build-ohcodec.sh'],root/'ffmpeg.log',env)
  host.verify(lock);host.verify_binding(lock,ndk,HERE)
  libraries=collect_libraries(root/'ffmpeg/prefix/lib',ndk/'llvm/bin/llvm-readelf')
  write(root/'build-complete.json',{'freshSourceAndBuildRoots':True,'sourcePins':sourcepins,'hostLockSHA256':sha(out/'host-lock.json'),'hostVerifiedAfter':True,'targetExecuted':False,'formalArtifactAllowed':False})
  return {'root':str(root),'ffmpeg':libraries,'smb':sha(dep/'sysroot/lib/libsmbclient.a')}
 try:
  with concurrent.futures.ThreadPoolExecutor(max_workers=a.parallel) as pool:r=list(pool.map(build,['origin-a','longer-absolute-directory-b']))
  for pin in sourcepins:require_sha(pin['path'],pin['sha256'])
  write(out/'comparison.json',{'runs':r,'ffmpegBytesEqual':r[0]['ffmpeg']==r[1]['ffmpeg'],'smbBytesEqual':r[0]['smb']==r[1]['smb'],'sameOldHashesRequired':False})
  if r[0]['ffmpeg']!=r[1]['ffmpeg'] or r[0]['smb']!=r[1]['smb']:raise ValueError('fresh-root reproducibility difference; investigate and report')
  write(out/'status.json',{'status':'builds_complete','formalArtifactAllowed':False,'deviceAcceptanceStatus':'pending'})
 except Exception as e:write(out/'status.json',{'status':'failed','error':str(e)});raise
if __name__=='__main__':main()
