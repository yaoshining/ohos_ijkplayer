import json,sys,sysconfig,subprocess,importlib.util
from pathlib import Path
from input_gate import sha
R=Path(__file__).resolve().parents[1];S=Path('/Applications/DevEco-Studio.app/Contents/sdk/default/openharmony/native');rows=[]
def pin(p,role):
 p=Path(p)
 if p.is_file():rows.append({'path':str(p),'realpath':str(p.resolve()),'size':p.stat().st_size,'sha256':sha(p),'role':role})
for name in ['clang','clang++','ld.lld','llvm-ar','llvm-ranlib','llvm-strip','llvm-readelf','llvm-objdump','llvm-nm']:pin(S/'llvm/bin'/name,'target compiler tools')
for p in [S/'build-tools/cmake/bin/cmake',S/'build-tools/cmake/bin/ninja',Path(sys.executable),Path('/Users/yaoshining/anaconda3/bin/python'),Path('/Users/yaoshining/anaconda3/bin/meson'),Path('/opt/homebrew/bin/pkg-config'),Path('/usr/bin/gperf'),Path('/usr/bin/make'),Path('/usr/bin/git'),Path('/usr/bin/xcrun')]:pin(p,'host tool')
for tree,role in [(S/'sysroot','prebuilt target SDK'),(S/'llvm/lib','compiler resources and host libraries'),(S/'build','SDK CMake'),(S/'build-tools/cmake/share','CMake modules')]:
 for p in sorted(tree.rglob('*')):pin(p,role)
lib=Path(sysconfig.get_path('stdlib'))
for p in sorted(lib.rglob('*')):
 if any(x in p.relative_to(lib).parts for x in ['site-packages','__pycache__']):continue
 pin(p,'Python standard library; bytecode disabled')
for mod in ['mesonbuild','mako','markupsafe']:
 spec=importlib.util.find_spec(mod)
 if spec:
  for p in sorted(Path(spec.origin).parent.rglob('*')):
   if '__pycache__' not in p.parts:pin(p,'Python module '+mod)
for file in [Path(sys.executable).parent.parent/'lib/libpython3.10.dylib'] :pin(file,'Python runtime')
clang=Path(subprocess.check_output(['/usr/bin/xcrun','--find','clang'],text=True).strip());pin(clang,'native generator compiler');pin(clang.parent/'clang++','native generator C++ compiler')
macsdk=Path(subprocess.check_output(['/usr/bin/xcrun','--show-sdk-path'],text=True).strip())
for p in sorted((macsdk/'usr/include').rglob('*')):pin(p,'native generator platform headers')
for p in sorted((clang.parent.parent/'clang').rglob('*')):pin(p,'native compiler resources')
for p in sorted((clang.parent.parent).glob('*.dylib')):pin(p,'native compiler shared library')
d={'prebuiltBoundary':'Compiler, platform SDK/runtime and host OS are pinned binary inputs, not source rebuilt','tools':rows,'nativeClang':str(clang),'nativeSDK':str(macsdk),'SDK':str(S),'python':sys.executable}
(R/'locks/tools-before.json').write_text(json.dumps(d,indent=2)+'\n');print('Pinned',len(rows),'tool/platform/module files')
