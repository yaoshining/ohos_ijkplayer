"""Reuse approved SDK overlay and exact public source archives in fresh CI roots."""
from pathlib import Path
import argparse,json,subprocess,sys,tarfile,shutil,importlib.util
import build
HERE=Path(__file__).resolve().parent;OLD=HERE.parent/'phase18'
def module(name,path):
 s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def extract(archive,dest):
 dest.mkdir(parents=True,exist_ok=False)
 with tarfile.open(archive) as t:
  for m in t:
   if Path(m.name).is_absolute() or '..' in Path(m.name).parts:raise ValueError('archive path escape')
  t.extractall(dest,filter='data')
def main():
 p=argparse.ArgumentParser();p.add_argument('--native-only',action='store_true');a=p.parse_args();out=Path('out/phase20-ci/inputs').resolve();out.mkdir(parents=True,exist_ok=False)
 fetch=module('fetch',HERE/'recipe/fetch-sources.py');sources=json.loads((HERE/'recipe/dependency-sources.lock.json').read_text())['sources'];cache=out/'cache'
 for row in sources:
  if not a.native_only or row['name']=='samba-4.20.7':fetch.fetch(row,cache)
 if a.native_only:return
 lock=json.loads((HERE/'recipe/producer-inputs.lock.json').read_text());repo=out/'ffmpeg.git';subprocess.run(['git','init','--bare',repo],check=True);subprocess.run(['git','-C',repo,'fetch','--depth=1',lock['ffmpeg']['repository'],lock['ffmpeg']['revision']],check=True)
 ff=out/'ffmpeg.tar'
 with ff.open('wb') as f:subprocess.run(['git','-C',repo,'archive',lock['ffmpeg']['revision']],stdout=f,check=True)
 build.require_sha(ff,lock['ffmpeg']['gitArchiveSha256'])
 # Exact approved Phase18 API24 overlay; keep Linux compiler identity distinct.
 bundle=next(b for b in json.loads((OLD/'inputs/bundles.json').read_text()) if b['name']=='target-sdk');overlay_archive=out/bundle['archive']
 with overlay_archive.open('wb') as f:
  for part in bundle['parts']:
   src=OLD/'inputs'/part['file'];build.require_sha(src,part['sha256']);assert src.stat().st_size==part['size'];f.write(src.read_bytes())
 build.require_sha(overlay_archive,bundle['sha256']);overlay=out/'overlay';extract(overlay_archive,overlay)
 tool=json.loads((OLD/'toolchain-lock.json').read_text());archive=out/'linux-sdk.tar.gz';subprocess.run(['curl','-fL','--retry','3','--max-time','1200',tool['url'],'-o',archive],check=True);build.require_sha(archive,tool['sha256'])
 with tarfile.open(archive) as t:
  members=[m for m in t.getmembers() if m.name.endswith('.zip') and '/native-linux-x64-' in m.name];assert len(members)==1
  with (out/'native.zip').open('wb') as f:shutil.copyfileobj(t.extractfile(members[0]),f)
 module('sdk_zip',OLD/'sdk_zip.py').extract_native_zip(out/'native.zip',out/'unpacked');c=list((out/'unpacked').rglob('llvm/bin/clang'));assert len(c)==1;c[0].parents[2].rename(out/'sdk');sdk=out/'sdk'
 for name in ['sysroot','llvm/include/c++','llvm/include/libcxx-ohos','llvm/lib/aarch64-linux-ohos','llvm/lib/clang/15.0.4/include','llvm/lib/clang/15.0.4/lib/aarch64-linux-ohos','build/cmake']:
  dest=sdk/name
  if dest.is_symlink() or dest.is_file():dest.unlink()
  elif dest.is_dir():shutil.rmtree(dest)
 for row in json.loads((overlay/'target-sdk.json').read_text())['files']:
  src=overlay/row['path'];build.require_sha(src,row['sha256']);dest=sdk/row['path'];dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(src,dest)
 build.write(out/'sdk-binding.json',{'linuxCompilerArchive':tool,'targetOverlaySHA256':bundle['sha256'],'targetManifestSHA256':build.sha(overlay/'target-sdk.json'),'formalArtifactAllowed':False})
 extract(ff,out/'test-ffmpeg');samba=next(r for r in sources if r['name']=='samba-4.20.7');extract(cache/samba['archiveFile'],out/'test-samba')
 with Path(__import__('os').environ['GITHUB_ENV']).open('a') as f:f.write('PHASE20_FFMPEG_SOURCE='+str(out/'test-ffmpeg')+'\nPHASE20_SAMBA_SOURCE='+str(out/'test-samba'/samba['archivePrefix'])+'\n')
if __name__=='__main__':main()
