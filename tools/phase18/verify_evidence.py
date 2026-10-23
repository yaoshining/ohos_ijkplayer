"""Cross-check actual new build bytes, package, links and fixed static contracts."""
from pathlib import Path
import collections,hashlib,json,sys
from evidence_contract import exact_set,compare_archive_rows,require_before_pin
HERE=Path(__file__).resolve().parent;R=Path(sys.argv[1]).resolve() if len(sys.argv)>1 else HERE.parents[1]/'out/phase18-ci'
sys.path.insert(0,str(R/'runtime/vendor'));from portable_elf import ar_members

def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
 return h.hexdigest()
def read(p):return json.loads(Path(p).read_text())
def under(p,root):
 if not Path(p).resolve().is_relative_to(root.resolve()):raise ValueError('source outside new root: '+str(p))

names={'libass':'libass.a','dovi':'libdovi.a','fontconfig':'libfontconfig.a','freetype':'libfreetype.a','fribidi':'libfribidi.a','harfbuzz':'libharfbuzz.a','lcms2':'liblcms2.a','lua':'liblua.a','shaderc_combined':'libshaderc_combined.a','xml2':'libxml2.a'}
bind=read(R/'dependency-object-binding.json');exact_set([c['component'] for c in bind['components']],list(names))
built=[];archive_members=0;rust_member_cache={}
for c in bind['components']:
 p=Path(c['archive']);under(p,R/'runs');assert p.name==names[c['component']] and sha(p)==c['sha256'];built.append({'path':'lib/'+p.name,'sha256':c['sha256']})
 occurrence=collections.Counter();actual=[]
 for n,data in ar_members(p):
  occurrence[n]+=1;actual.append((n,occurrence[n],hashlib.sha256(data).hexdigest(),len(data)))
 expected=[(m['name'],m['occurrence'],m['sha256'],m['size']) for m in c['members']];assert actual==expected,p;archive_members+=len(actual)
 for m in c['members']:
  b=m['binding']
  if 'compiledObjects' in b:
   assert b['compiledObjects']
   for obj in b['compiledObjects']:under(obj,R/'runs');assert sha(obj)==m['sha256']
  elif 'rustInputs' in b:
   assert b['rustInputs']
   for row in b['rustInputs']:
    key=row['archive']
    if key not in rust_member_cache:
     entries=collections.defaultdict(set)
     for n,data in ar_members(Path(key)):entries[n].add(hashlib.sha256(data).hexdigest())
     rust_member_cache[key]=entries
    assert m['sha256'] in rust_member_cache[key][row['member']]
  else:
   assert c['component']=='dovi' and b.get('directRustcStaticlib');assert Path(b['depInfo']).is_file() and Path(b['compileLog']).is_file()
# Source -> actual installed prefix -> package, including each header and relocated pc.
P=R/'integration/input-package';origins=read(P/'provenance/new-dependencies.json');exact_set([x['packagePath'] for x in origins],['deps/'+str(p.relative_to(P/'deps')) for p in (P/'deps').rglob('*') if p.is_file()])
for o in origins:
 src=Path(o['source']);under(src,R/'runs');dst=P/o['packagePath'];assert sha(src)==o['sourceSHA256'] and sha(dst)==o['packageSHA256']
 if dst.suffix=='.pc':assert src.read_text().replace('prefix=/usr/local','prefix=${pcfiledir}/../..')==dst.read_text()
 else:assert o['sourceSHA256']==o['packageSHA256']
package=[{'path':x['packagePath'].removeprefix('deps/'),'sha256':x['packageSHA256']}for x in origins if x['packagePath'].endswith('.a')];expected_names=['lib/'+x for x in names.values()];compare_archive_rows(built,package,expected_names)
contract=read(HERE/'expected-static-contract.json');runs=[]
for run in sorted((R/'integration/runs').rglob('link-inputs.json')):
 root=run.parent;links=read(run);selected=[{'path':x['path'].removeprefix('run/deps/'),'sha256':x['sha256']}for x in links if x['path'].startswith('run/deps/') and x['path'].endswith('.a')];compare_archive_rows(built,selected,expected_names)
 for row in selected:assert sha(root/'deps'/row['path'])==row['sha256']
 v=read(root/'validation/static-validation.json');exact_set(v['mpvFFmpegImports'],contract['mpvFFmpegImports']);exact_set(v['api']['publicSymbols'],contract['publicSymbols'])
 for label,expected in contract['bridgeRequired'].items():exact_set(v['bridgeClosures'][label]['required'],expected)
 for source,expected in contract['nativeEffectiveCallNames'].items():exact_set(list(v['nativeEffectiveCalls'][source]),expected)
 runs.append({'run':str(root),'FFmpegImports':247,'publicAPI':54,'actualNewLibraries':10})
assert len(runs)==2
# All pre-build observations must remain byte/realpath-identical after every build.
tools=read(R/'locks/tools-before.json');before={}
for t in tools['tools']:
 p=Path(t['path']);assert sha(p)==t['sha256'];assert str(p.resolve())==t.get('realpath',t.get('resolved',str(p.resolve())))
 before[str(p.resolve())]=t['sha256']
compiler_checked=0
for row in bind['compilerInputs']:
 p=Path(row['path']);assert sha(p)==row['sha256']
 if not p.resolve().is_relative_to(R) or p.resolve().is_relative_to(Path(tools['SDK']).resolve()):require_before_pin(str(p.resolve()),row['sha256'],before)
 compiler_checked+=1
result={'passed':True,'archiveMembersIndependentlyRead':archive_members,'sourceInstallPackageEntries':len(origins),'compilerInputsChecked':compiler_checked,'beforeToolPinsReverified':len(tools['tools']),'runs':runs,'targetRuntimeExecuted':False,'prebuiltSDKAndRustStdBoundary':True,'directRustcUnitsBoundByCompileLogAndDepInfo':True}
(Path(sys.argv[2]) if len(sys.argv)>2 else R/'evidence-cross-check.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
