from pathlib import Path
import json,subprocess,sys,os,shutil,tarfile,zipfile,hashlib,importlib.util,sysconfig,platform
HERE=Path(__file__).resolve().parent;REPO=HERE.parents[1];OUT=REPO/'out/phase18-ci';assert not OUT.exists();OUT.mkdir(parents=True)
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
 return h.hexdigest()
def extract_regular(archive,dest):
 dest.mkdir(parents=True,exist_ok=True)
 with tarfile.open(archive) as t:
  seen=set()
  for m in t:
   n=Path(m.name)
   if n.is_absolute() or '..' in n.parts or m.name in seen or not m.isfile():raise ValueError('unsafe/nonregular/duplicate bundle')
   seen.add(m.name);p=dest/n;p.parent.mkdir(parents=True,exist_ok=True)
   with p.open('wb') as f:shutil.copyfileobj(t.extractfile(m),f)
   p.chmod(m.mode)
def download(url,dest,digest):
 subprocess.run(['curl','--http1.1','-fL','--retry','3','--connect-timeout','30','--max-time','1200',url,'-o',str(dest)],check=True)
 if sha(dest)!=digest:raise ValueError('download digest mismatch '+dest.name)
for bundle in json.loads((HERE/'inputs/bundles.json').read_text()):
 a=OUT/bundle['archive']
 with a.open('wb') as f:
  for part in bundle['parts']:
   p=HERE/'inputs'/part['file'];assert p.stat().st_size==part['size'] and sha(p)==part['sha256'];f.write(p.read_bytes())
 assert a.stat().st_size==bundle['size'] and sha(a)==bundle['sha256'];extract_regular(a,OUT if bundle['name']=='sources' else OUT/'target-overlay')
# Published scripts are the executable recipe authority; bundled snapshots remain recorded.
shutil.copytree(HERE/'runtime',OUT/'runtime',dirs_exist_ok=True);shutil.copytree(HERE/'tests',OUT/'tests');shutil.copyfile(HERE/'baseline-provenance.json',OUT/'baseline-provenance.json')
lock=json.loads((HERE/'toolchain-lock.json').read_text());a=OUT/'linux-sdk.tar.gz';download(lock['url'],a,lock['sha256'])
with tarfile.open(a) as t:
 members=[m for m in t.getmembers() if m.name.endswith('.zip') and '/native-linux-x64-' in m.name];assert len(members)==1
 with (OUT/'native.zip').open('wb') as f:shutil.copyfileobj(t.extractfile(members[0]),f)
spec=importlib.util.spec_from_file_location('sdk_zip',HERE/'sdk_zip.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);m.extract_native_zip(OUT/'native.zip',OUT/'unpacked');c=list((OUT/'unpacked').rglob('llvm/bin/clang'));assert len(c)==1;c[0].parents[2].rename(OUT/'sdk');sdk=OUT/'sdk'
for name in ['sysroot','llvm/include/c++','llvm/include/libcxx-ohos','llvm/lib/aarch64-linux-ohos','llvm/lib/clang/15.0.4/include','llvm/lib/clang/15.0.4/lib/aarch64-linux-ohos','build/cmake']:
 p=sdk/name
 if p.is_symlink():p.unlink()
 elif p.is_dir():shutil.rmtree(p)
 elif p.exists():p.unlink()
overlay=OUT/'target-overlay';target=json.loads((overlay/'target-sdk.json').read_text())
for row in target['files']:
 p=overlay/row['path'];assert sha(p)==row['sha256'];dest=sdk/row['path'];dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,dest)
# Official Ninja 1.12.0, exact archive hash; never nonexistent PyPI ninja==1.12.0.
nl=json.loads((HERE/'ninja-lock.json').read_text());download(nl['url'],OUT/'ninja.zip',nl['archiveSHA256'])
with zipfile.ZipFile(OUT/'ninja.zip') as z:data=z.read('ninja')
assert hashlib.sha256(data).hexdigest()==nl['binarySHA256']
ninja=sdk/'build-tools/cmake/bin/ninja';ninja.write_bytes(data);ninja.chmod(0o755)
# New isolated Rust compiler/std prefix from exact published distributions.
rustlock=json.loads((HERE/'rust-linux-lock.json').read_text());rust=OUT/'dovi-input/toolchain';rust.mkdir();tools=OUT/'dovi-input/tools';tools.mkdir()
for row in rustlock['archives']:
 archive=OUT/(row['package']+'-'+row['target']+'.tar.'+('gz' if row['package']=='cargo-c' else 'xz'));download(row['url'],archive,row['sha256']);dest=OUT/('extract-'+row['package']+'-'+row['target']);dest.mkdir()
 with tarfile.open(archive) as t:
  for m in t:
   n=Path(m.name)
   if n.is_absolute() or '..' in n.parts:raise ValueError('distribution path escape')
  t.extractall(dest,filter='data') if sys.version_info>=(3,12) else t.extractall(dest)
 if row['package']=='cargo-c':
  for name in ['cargo-cinstall','cargo-cbuild']:
   p=list(dest.rglob(name));assert len(p)==1;shutil.copy2(p[0],tools/name)
 else:
  install=list(dest.rglob('install.sh'));assert len(install)==1;subprocess.run(['bash',str(install[0]),'--prefix='+str(rust),'--disable-ldconfig'],check=True)
# Pin actual host tools, Python modules, GCC inputs and target SDK BEFORE build.
rows=[];seen=set()
def pin(p,role):
 p=Path(p)
 if not p.is_file() or str(p) in seen:return
 seen.add(str(p));rows.append({'path':str(p),'realpath':str(p.resolve()),'size':p.stat().st_size,'sha256':sha(p),'role':role})
for tree,role in [(sdk,'mixed diagnostic SDK'),(rust,'prebuilt Rust compiler and std'),(tools,'prebuilt cargo-c/cbindgen'),(Path('/usr/include'),'native generator platform'),(Path('/usr/lib/gcc'),'native GCC internals')]:
 for p in sorted(tree.rglob('*')):pin(p,role)
for name in ['python3','meson','pkg-config','gcc','g++','ar','strip','gperf','make','git','ld']:
 p=shutil.which(name);assert p,name;pin(p,'host tool')
stdlib=Path(sysconfig.get_path('stdlib'))
for p in sorted(stdlib.rglob('*')):
 if any(x in p.parts for x in ['site-packages','dist-packages','__pycache__']):continue
 pin(p,'Python standard library')
for name in ['mesonbuild','mako','markupsafe']:
 spec=importlib.util.find_spec(name)
 if spec:
  for p in sorted(Path(spec.origin).parent.rglob('*')):
   if '__pycache__' not in p.parts:pin(p,'Python module '+name)
for p in Path('/lib/x86_64-linux-gnu').glob('*.so*'):pin(p,'host shared libraries')
versions={name:subprocess.check_output([shutil.which(name),'--version'],text=True).splitlines()[0] for name in ['python3','meson','pkg-config','gcc','gperf','make']}
tooldata={'SDK':str(sdk),'nativeSDK':'/usr','nativeClang':shutil.which('gcc'),'nativeCXX':shutil.which('g++'),'nativeCompilerArgs':[],'meson':shutil.which('meson'),'pkgConfig':shutil.which('pkg-config'),'python':sys.executable,'tools':rows,'versions':versions,'platform':platform.platform(),'toolchainBoundary':'prebuilt host/compiler/std/platform inputs; not source bootstrap'};(OUT/'locks/tools-before.json').write_text(json.dumps(tooldata,indent=2)+'\n');(OUT/'platform-binding.json').write_text(json.dumps({'hostSDK':lock,'targetManifestSHA256':sha(overlay/'target-sdk.json'),'rustDistributions':rustlock,'targetRuntime':'pending','formalArtifactAllowed':False},indent=2)+'\n')
print('Phase18 bootstrap complete',len(rows),'tool inputs')
