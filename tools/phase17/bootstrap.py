#!/usr/bin/env python3
from pathlib import Path
import hashlib,json,shutil,subprocess,tarfile,importlib.util,platform
HERE=Path(__file__).resolve().parent;REPO=HERE.parents[1];OUT=REPO/'out/phase17-ci'
assert not OUT.exists();OUT.mkdir(parents=True)
def sha(p):
 h=hashlib.sha256()
 with p.open('rb')as f:
  for block in iter(lambda:f.read(1024*1024),b''):h.update(block)
 return h.hexdigest()
def extract_regular(archive,dest):
 assert not dest.exists();dest.mkdir()
 with tarfile.open(archive)as t:
  seen=set()
  for m in t:
   n=Path(m.name)
   if n.is_absolute()or'..'in n.parts or m.name in seen or not m.isfile():raise ValueError('non-regular/unsafe/duplicate bundle entry')
   seen.add(m.name);p=dest/n;p.parent.mkdir(parents=True,exist_ok=True)
   with p.open('wb')as f:shutil.copyfileobj(t.extractfile(m),f)
   p.chmod(m.mode)
for bundle in json.loads((HERE/'inputs/bundles.json').read_text()):
 p=OUT/bundle['archive']
 with p.open('wb')as f:
  for part in bundle['parts']:
   q=HERE/'inputs'/part['file'];assert q.stat().st_size==part['size']and sha(q)==part['sha256'];f.write(q.read_bytes())
 assert p.stat().st_size==bundle['size']and sha(p)==bundle['sha256']
 extract_regular(p,OUT/('input-package'if p.name=='inputs.tar.gz'else'target-overlay'))
lock=json.loads((HERE/'toolchain-lock.json').read_text());archive=OUT/'linux-sdk.tar.gz'
cmd=['curl','--http1.1','-fL','--retry','3','--connect-timeout','30','--max-time','1200',lock['url'],'-o',str(archive)]
subprocess.run(cmd,check=True);assert sha(archive)==lock['sha256'],'Linux SDK archive SHA mismatch'
with tarfile.open(archive)as t:
 matches=[m for m in t.getmembers()if m.name.endswith('.zip')and'/native-linux-x64-'in m.name];assert len(matches)==1
 with (OUT/'native.zip').open('wb')as f:shutil.copyfileobj(t.extractfile(matches[0]),f)
spec=importlib.util.spec_from_file_location('locked_zip_helper',REPO/'tools/ffmpeg8/ci-prepare-inputs.py');helper=importlib.util.module_from_spec(spec);spec.loader.exec_module(helper);helper.extract_native_zip(OUT/'native.zip',OUT/'unpacked')
compilers=list((OUT/'unpacked').rglob('llvm/bin/clang'));assert len(compilers)==1;sdk=compilers[0].parents[2];sdk.rename(OUT/'sdk');sdk=OUT/'sdk'
old_metadata=(sdk/'oh-uni-package.json').read_text() if(sdk/'oh-uni-package.json').exists()else None
# Remove only newly extracted target inputs; keep the downloaded Linux host tools/libraries.
for name in ['sysroot','llvm/include/c++','llvm/include/libcxx-ohos','llvm/lib/aarch64-linux-ohos','llvm/lib/clang/15.0.4/include','llvm/lib/clang/15.0.4/lib/aarch64-linux-ohos']:
 p=sdk/name
 if p.is_symlink():p.unlink()
 elif p.is_dir():shutil.rmtree(p)
 elif p.exists():p.unlink()
overlay=OUT/'target-overlay';target=json.loads((overlay/'target-sdk.json').read_text())
for row in target['files']:
 p=overlay/row['path'];assert sha(p)==row['sha256']and p.stat().st_size==row['size'];q=sdk/row['path'];q.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,q)
versions={}
for name in ['clang','clang++','ld.lld']:
 p=sdk/'llvm/bin'/name;versions[name]={'sha256':sha(p),'version':subprocess.check_output([str(p),'--version'],text=True)}
(OUT/'platform-binding.json').write_text(json.dumps({'platform':platform.platform(),'hostSdkArchive':lock,'hostSdkOriginalMetadata':old_metadata,'targetOverlayManifestSHA256':sha(overlay/'target-sdk.json'),'targetScope':target['scope'],'tools':versions,'identity':'OpenHarmony 5.0 Linux host clang + pinned API24 target headers/libraries from Phase16; diagnostic mixed SDK, not the macOS toolchain','formalArtifactAllowed':False},indent=2)+'\n')
print(json.dumps({'sdk':str(sdk),'inputs':str(OUT/'input-package'),'hostSdkArchiveVerified':True,'API24TargetInputsVerified':True},indent=2))

# The configuration probes link C++ executables but never run target ARM64 code.
probe=OUT/'target-cxx-probe';probe.mkdir();source=probe/'main.cpp';source.write_text('int main() { return 0; }\n')
argv=[str(sdk/'llvm/bin/clang++'),'--target=aarch64-linux-ohos','--sysroot='+str(sdk/'sysroot'),'-fuse-ld=lld','-lc++_shared','-lvulkan','-Wl,--allow-shlib-undefined','-Wl,--trace',str(source),'-o',str(probe/'probe')]
with (probe/'link.log').open('w')as log:result=subprocess.run(argv,stdout=log,stderr=subprocess.STDOUT)
(probe/'result.json').write_text(json.dumps({'argv':argv,'exitCode':result.returncode,'targetExecuted':False},indent=2)+'\n')
assert result.returncode==0,'default C++ Vulkan configure probe failed; see target-cxx-probe/link.log'
