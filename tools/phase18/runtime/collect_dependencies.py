from pathlib import Path
import json,sys,shlex,hashlib,collections,re,subprocess
from input_gate import sha,inventory
sys.path.insert(0,str(Path(__file__).parent/'vendor'));from portable_elf import ar_members;from ninja_deps import parse_ninja_deps
R=Path(__file__).resolve().parents[1];tool=json.loads((R/'locks/tools-before.json').read_text());S=Path(tool['SDK']);MS=Path(tool['nativeSDK']);MC=Path(tool['nativeClang']).parents[1]
files={};objects={};builds=[];unbuilt=[]
def pin(p,role):
 p=Path(p).resolve()
 if not any(p.is_relative_to(root) for root in [R,S,MS,MC]):raise ValueError('undeclared dependency '+str(p))
 key=str(p);row={'path':key,'sha256':sha(p),'size':p.stat().st_size,'role':role}
 if key in files and files[key]['sha256']!=row['sha256']:raise ValueError('input drift')
 files[key]=row;return key
for run,stages in [(R/'runs'/('native-02' if (R/'runs/native-02').exists() else 'native-01'),['harfbuzz','fribidi','lcms2','xml2','freetype','fontconfig','libass']),(R/'runs/shaderc-01',['shaderc'])]:
 for stage in stages:
  b=run/'build'/stage if stage!='shaderc' else run/'build';db=b/'compile_commands.json';dp=run/'logs'/(stage+'-deps.log' if stage!='shaderc' else 'deps.log')
  blocks=parse_ninja_deps(dp.read_text());commands=json.loads(db.read_text());built=set()
  for cmd in commands:
   args=shlex.split(cmd['command']);obj=(Path(cmd['directory'])/cmd.get('output',args[args.index('-o')+1])).resolve()
   if not obj.exists():unbuilt.append(str(obj));continue
   source=(Path(cmd['directory'])/cmd['file']).resolve();rel=str(obj.relative_to(b));deps=blocks.get(rel)
   if deps is None:raise ValueError('missing actual ninja deps '+str(obj))
   depkeys=[pin(b/n,'source-or-header') for n in deps];assert str(source) in depkeys
   key=pin(obj,'compiled-object');objects[key]={'objectSHA256':files[key]['sha256'],'source':str(source),'command':cmd,'dependencies':depkeys};built.add(rel)
  for output in set(blocks)-built:
   command=subprocess.check_output([str(S/'build-tools/cmake/bin/ninja'),'-C',str(b),'-t','commands',output],text=True).strip()
   if not output.endswith('.i') or ' -E ' not in command:raise ValueError('unbound actual dependencies '+output)
   dependencies=[pin(b/n,'preprocessor-generator-input') for n in blocks[output]]
   pin(b/output,'preprocessor-generated-output');builds.append({'generated':str(b/output),'command':command,'dependencies':dependencies})
  builds.append({'component':stage,'objects':len(built),'databaseSHA256':sha(db),'depsSHA256':sha(dp)})
# Lua's stock make rule has no compiler depfile. Reconstruct includes using the exact compile argv,
# after source/SDK pins were captured before build and reverified; do not call this a historical read trace.
run=R/'runs'/('native-02' if (R/'runs/native-02').exists() else 'native-01');b=run/'build/lua/src';log=(run/'logs/lua-build.log').read_text();luarows=[]
for line in log.splitlines():
 args=shlex.split(line)
 if not args or args[0]!=str(S/'llvm/bin/clang') or '-c' not in args or '-o' not in args:continue
 oi=args.index('-o');obj=b/args[oi+1];source=(b/args[-1]).resolve();depfile=b/(obj.stem+'.postbuild-deps.d')
 depcmd=args[:];del depcmd[oi:oi+2];depcmd[depcmd.index('-c')]='-M';depcmd+=['-MF',str(depfile)]
 subprocess.run(depcmd,cwd=b,check=True,stdout=subprocess.DEVNULL,stderr=subprocess.PIPE)
 raw=depfile.read_text().replace('\\\n',' ');deps=shlex.split(raw.split(':',1)[1]);depkeys=[pin(b/n,'lua-postbuild-source-or-header') for n in deps];key=pin(obj,'compiled-object');objects[key]={'objectSHA256':sha(obj),'source':str(source),'command':args,'dependencies':depkeys,'dependencyObservation':'postbuild reconstruction using original compile argv, unchanged pinned source/SDK'};luarows.append({'object':key,'dependencyCommand':depcmd,'depfileSHA256':sha(depfile)})
assert len(luarows)==32,len(luarows)
# Bind Rust component crate objects and prebuilt std members independently of final staticlib.
rust={};rust_inputs=[]
for root,role in [(R/'runs/dovi-01/target-ohos/aarch64-unknown-linux-ohos/release/deps','fresh-rust-crate'),(R/'dovi-input/toolchain/lib/rustlib/aarch64-unknown-linux-ohos/lib','prebuilt-target-stdlib')]:
 for p in sorted(root.glob('*.rlib')):
  rust_inputs.append({'path':str(p),'sha256':sha(p),'role':role})
  for n,data in ar_members(p):
   if data.startswith(b'\x7fELF'):rust.setdefault(hashlib.sha256(data).hexdigest(),[]).append({'archive':str(p),'member':n,'role':role})
bysha=collections.defaultdict(list)
for p,o in objects.items():bysha[o['objectSHA256']].append(p)
components=[];old=json.loads(((R/'baseline-provenance.json') if (R/'baseline-provenance.json').exists() else (R.parent/'phase17/provenance/provenance-matrix.json')).read_text())['components']
for c in old:
 name=c['component'];filename=Path(c['archives']['phase16Staged']['path']).name;root=R/('runs/dovi-01/install/usr/local' if name=='dovi' else 'runs/shaderc-01/prefix' if name=='shaderc_combined' else ('runs/native-02/prefix' if (R/'runs/native-02').exists() else 'runs/native-01/prefix'));p=root/'lib'/filename;members=[];count=collections.Counter()
 for n,data in ar_members(p):
  count[n]+=1;digest=hashlib.sha256(data).hexdigest();assert data[:4]==b'\x7fELF',n;assert int.from_bytes(data[18:20],'little')==183,n
  binding={'compiledObjects':bysha[digest]} if digest in bysha else {'rustInputs':rust[digest]} if digest in rust else None
  if binding is None and name=='dovi' and n.startswith(next((R/'runs/dovi-01/target-ohos/aarch64-unknown-linux-ohos/release/deps').glob('dovi-*.d')).stem+'.'):
   # rustc emits this crate's codegen units directly inside --crate-type staticlib.
   binding={'directRustcStaticlib':True,'compileLog':str(R/'runs/dovi-01/logs/cinstall.log'),'depInfo':str(next((R/'runs/dovi-01/target-ohos/aarch64-unknown-linux-ohos/release/deps').glob('dovi-*.d')))}
  if binding is None:raise ValueError('unbound member '+name+':'+n)
  members.append({'name':n,'occurrence':count[n],'sha256':digest,'size':len(data),'binding':binding})
 components.append({'component':name,'archive':str(p),'sha256':sha(p),'members':members,'oldSHA256':c['archives']['phase16Staged']['sha256']})
result={'schemaVersion':1,'components':components,'compilerInputs':list(files.values()),'objects':objects,'ninjaBuilds':builds,'luaPostbuildDependencies':luarows,'rustArchiveInputs':rust_inputs,'unbuiltCompileDatabaseOutputs':unbuilt,'scope':'actual compile databases/Ninja deps/Cargo outputs plus pinned before-build source/tools; postbuild Lua reconstruction separately identified','oldHistoricalCacheFullyVerified':False,'targetRuntime':'pending'}
(R/'dependency-object-binding.json').write_text(json.dumps(result,indent=2)+'\n');print('Bound',sum(len(c['members']) for c in components),'members;',len(objects),'C/C++ objects;',len(files),'unique pins')
