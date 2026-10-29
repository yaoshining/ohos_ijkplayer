"""复用批准的源分片和 CI 制品，下载后严格复验再使用。"""
from pathlib import Path
import argparse,tarfile,zipfile,json,shutil,subprocess,importlib.util,os
from common import *
ARTIFACTS={
 'native':(12170137384,'a845ae7f4b933bbbf835f193eee8a85174c3fd6cd9a006d8f2263b0972ae4f5a','347a69b53bc7ba66a6f2a5eed3c92d67a116a7b7','39217268165'),
 'target':(12170679926,'cb99ae3a77eef2895af2221a2db216f360e3f2c466e1acd79e5eecbecb63ee77','ad0e403e4f7a3fb4d39bbb4c963d0d1994dad080','39218428737'),
 'mpv':(12148205047,'dbfac00c9880d3b6b46bd17b3ee0b31e2d0b673458ae983c7389649660bcdde9','2d65a50b3a4c3d09fdb925bcb92a2af307a1a704','39156616632')}
def module(name,p):
 s=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m

def download(kind,out):
 ident,digest,commit,runid=ARTIFACTS[kind];archive=out/(kind+'.zip')
 with archive.open('wb') as f:subprocess.run(['gh','api',f'repos/yaoshining/ohos_ijkplayer/actions/artifacts/{ident}/zip'],stdout=f,check=True,timeout=600,env=dict(ENV,GODEBUG='http2client=0'))
 require(archive,digest);dest=out/kind;dest.mkdir()
 with zipfile.ZipFile(archive) as z:
  names=[i.filename for i in z.infolist() if not i.is_dir()]
  if len(names)!=len(set(names)) or any(Path(n).is_absolute() or '..' in Path(n).parts for n in names):raise ValueError('unsafe ZIP')
  index=json.loads(z.read('evidence-index.json'));rows=index['files'];assert set(names)=={r['path'] for r in rows}|{'evidence-index.json'}
  for row in rows:
   data=z.read(row['path']);assert len(data)==row['size'] and __import__('hashlib').sha256(data).hexdigest()==row['sha256']
  z.extractall(dest)
 identity=json.loads((dest/'identity.json').read_text()) if (dest/'identity.json').is_file() else index
 assert identity.get('GITHUB_SHA',identity.get('commit'))==commit
 assert str(identity.get('GITHUB_RUN_ID',identity.get('runId')))==runid
 write(out/(kind+'-verification.json'),{'artifactId':ident,'zip':pin(archive),'commit':commit,'runId':runid,'fileCount':len(rows),'exactFileSet':True})
 return dest

def bundle(out,name):
 old=HERE.parent/'phase18';row=next(r for r in json.loads((old/'inputs/bundles.json').read_text()) if r['name']==name);archive=out/row['archive']
 with archive.open('wb') as f:
  for part in row['parts']:
   p=old/'inputs'/part['file'];require(p,part['sha256']);assert p.stat().st_size==part['size']
   with p.open('rb') as source:shutil.copyfileobj(source,f)
 require(archive,row['sha256']);return archive

def main():
 p=argparse.ArgumentParser();p.add_argument('--kind',choices=['native','target'],required=True);a=p.parse_args();out=Path('out/phase21-ci/inputs').resolve();out.mkdir(parents=True,exist_ok=False)
 archive=bundle(out,'sources');sources=out/'sources';sources.mkdir()
 prefixes=['integration/base/sources/mpv/','integration/base/sources/libplacebo/','integration/base/ffmpeg/include/','source-package/source/libass/']
 with tarfile.open(archive) as t:
  members=[m for m in t.getmembers() if any(m.name.startswith(x) for x in prefixes)]
  for m in members:
   if Path(m.name).is_absolute() or '..' in Path(m.name).parts or not(m.isdir() or m.isfile()):raise ValueError('unsafe source member '+m.name)
   dest=sources/m.name
   if m.isdir():dest.mkdir(parents=True,exist_ok=True)
   else:
    dest.parent.mkdir(parents=True,exist_ok=True)
    with dest.open('wb') as f:shutil.copyfileobj(t.extractfile(m),f)
    dest.chmod(m.mode&0o777)
 write(out/'source-binding.json',{'bundleSHA256':sha(archive),'files':tree(sources)})
 if a.kind=='native':
  download('native',out)
  ff=out/'ffmpeg.tar';repo=out/'ffmpeg.git';lock=json.loads((HERE.parent/'phase20/recipe/producer-inputs.lock.json').read_text())['ffmpeg']
  run(['git','init','--bare',repo],out/'git-init.log');run(['git','-C',repo,'fetch','--depth=1',lock['repository'],lock['revision']],out/'git-fetch.log')
  with ff.open('wb') as f:subprocess.run(['git','-C',repo,'archive',lock['revision']],stdout=f,check=True)
  require(ff,lock['gitArchiveSha256'])
  srcs=json.loads((HERE.parent/'phase20/recipe/dependency-sources.lock.json').read_text())['sources'];samba=next(r for r in srcs if r['name']=='samba-4.20.7');fetch=module('fetch',HERE.parent/'phase20/recipe/fetch-sources.py');fetch.fetch(samba,out/'cache')
  write(out/'native-source-lock.json',{'ffmpeg':lock,'samba':samba});return
 download('target',out);download('mpv',out)
 overlay_archive=bundle(out,'target-sdk');overlay=out/'overlay';extractor=module('extract',HERE.parent/'phase20/extract.py');extractor.extract_source(overlay_archive,overlay)
 tool=json.loads((HERE.parent/'phase18/toolchain-lock.json').read_text());archive=out/'linux-sdk.tar.gz';run(['curl','-fL','--retry','3','--max-time','1200',tool['url'],'-o',archive],out/'sdk-download.log',timeout=1500);require(archive,tool['sha256'])
 with tarfile.open(archive) as t:
  members=[m for m in t.getmembers() if m.name.endswith('.zip') and '/native-linux-x64-' in m.name];assert len(members)==1
  with (out/'native.zip').open('wb') as f:shutil.copyfileobj(t.extractfile(members[0]),f)
 module('sdk_zip',HERE.parent/'phase18/sdk_zip.py').extract_native_zip(out/'native.zip',out/'unpacked');c=list((out/'unpacked').rglob('llvm/bin/clang'));assert len(c)==1;c[0].parents[2].rename(out/'sdk');sdk=out/'sdk'
 for name in ['sysroot','llvm/include/c++','llvm/include/libcxx-ohos','llvm/lib/aarch64-linux-ohos','llvm/lib/clang/15.0.4/include','llvm/lib/clang/15.0.4/lib/aarch64-linux-ohos','build/cmake']:
  dest=sdk/name
  if dest.is_symlink() or dest.is_file():dest.unlink()
  elif dest.is_dir():shutil.rmtree(dest)
 for row in json.loads((overlay/'target-sdk.json').read_text())['files']:
  src=overlay/row['path'];require(src,row['sha256']);dest=sdk/row['path'];dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(src,dest)
 write(out/'sdk-binding.json',{'linuxCompilerArchive':tool,'targetOverlaySHA256':sha(overlay_archive),'targetManifestSHA256':sha(overlay/'target-sdk.json'),'targetExecuted':False})
if __name__=='__main__':main()
