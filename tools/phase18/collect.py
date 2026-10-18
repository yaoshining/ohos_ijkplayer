from pathlib import Path
import os,json,hashlib,shutil,subprocess
from evidence_contract import host_package_file
HERE=Path(__file__).resolve().parent;REPO=HERE.parents[1];R=REPO/'out/phase18-ci';D=REPO/'out/phase18-artifact';D.mkdir(parents=True,exist_ok=True)
selected=[]
for root in [R/'runs',R/'integration/runs',R/'locks']:
 if not root.exists():continue
 for p in root.rglob('*'):
  if not p.is_file() or any(x in p.parts for x in ['source','toolchain','home','cache','cargo-home','target-host-tests']):continue
  if p.suffix in ['.json','.log','.txt','.ini','.h','.pc','.d','.map'] or p.name in ['libass.a','libdovi.a','libfontconfig.a','libfreetype.a','libfribidi.a','libharfbuzz.a','liblcms2.a','liblua.a','libshaderc_combined.a','libxml2.a','libplacebo.a','libmpv.so','install-unstripped.so']:selected.append(p)
for folder in [R,R/'integration']:
 if folder.exists():selected += [p for p in folder.iterdir() if p.is_file() and p.suffix in ['.json','.log']]
for p in [R/'integration/input-package/package.json',R/'integration/input-package/provenance/new-dependencies.json',R/'source-package/source-final.json',R/'source-package/source-origins.json']:
 if p.exists():selected.append(p)
# Preserve actual objects and rlibs for independent downloaded member binding.
binding=R/'dependency-object-binding.json'
if binding.exists():
 b=json.loads(binding.read_text());selected += [Path(p) for p in b['objects']]
 selected += [Path(x['path']) for x in b['rustArchiveInputs']]
for run in (R/'integration/runs').rglob('selected-interop-inputs.json') if (R/'integration/runs').exists() else []:
 selected += [Path(x['object']) for x in json.loads(run.read_text())['inputs']]
for rel in ['source-package/source-original.json','source-package/source-final.json','source-package/source-origins.json','target-overlay/target-sdk.json','dovi-input/source/dolby_vision/Cargo.lock','dovi-input/copy-binding.json']:
 p=R/rel
 if p.is_file():selected.append(p)
for sub in ['source-package/patches','dovi-input/vendor']:
 root=R/sub
 if root.exists():selected += [p for p in root.rglob('*') if p.is_file() and (sub.endswith('patches') or p.name=='.cargo-checksum.json')]
package=R/'integration/input-package'
if (package/'provenance/new-dependencies.json').exists():selected += [package/x['packagePath'] for x in json.loads((package/'provenance/new-dependencies.json').read_text())]
for p in sorted(set(selected)):
 if not p.is_file():continue
 dest=D/p.relative_to(R);dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,dest)
# Executed recipes and exact CI commit files (no source chunks duplicated here).
for base,destroot in [(HERE,D/'execution/published'),(R/'runtime',D/'execution/runtime'),(R/'integration/runtime',D/'execution/integration-runtime'),(REPO/'out/phase18-host',D/'host-bootstrap')]:
 if not base.exists():continue
 for p in base.rglob('*'):
  rel=p.relative_to(base)
  if any(x in rel.parts for x in ['venv','__pycache__','inputs','partial']):continue
  if destroot.name=='host-bootstrap' and rel.parts[0] in ['debs','wheels'] and not host_package_file(str(rel)):continue
  if not p.is_file():continue
  dest=destroot/p.relative_to(base);dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,dest)
# License texts for the exact source/tool distributions consumed by this run.
license_rows=[]
for root,label in [(R/'source-package/source','native-sources'),(R/'dovi-input/vendor','rust-vendor'),(R/'dovi-input/source','dovi-source'),(R/'sdk','diagnostic-sdk'),(R/'dovi-input/toolchain/share/doc/rust','rust-toolchain')]:
 if not root.exists():continue
 for p in root.rglob('*'):
  if not p.is_file() or not p.name.lower().startswith(('license','licence','copying','copyright','notice')):continue
  dest=D/'licenses'/label/p.relative_to(root);dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,dest)
  license_rows.append({'source':str(p),'artifactPath':str(dest.relative_to(D)),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
lua=R/'source-package/source/lua/doc/readme.html'
if lua.is_file():
 dest=D/'licenses/native-sources/lua/doc/readme.html';dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(lua,dest)
 license_rows.append({'source':str(lua),'artifactPath':str(dest.relative_to(D)),'sha256':hashlib.sha256(lua.read_bytes()).hexdigest(),'note':'Lua MIT license is inside official readme'})
(D/'license-evidence.json').write_text(json.dumps({'files':license_rows,'scope':'Observed exact distribution license texts; not legal approval or toolchain source bootstrap'},indent=2)+'\n')
workflow=REPO/'.github/workflows/phase18-dependency-closure.yml';dest=D/'execution/workflow.yml';dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(workflow,dest)
rows=[]
for p in sorted(D.rglob('*')):
 if p.is_file() and p!=D/'evidence-index.json':rows.append({'path':str(p.relative_to(D)),'size':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
(D/'evidence-index.json').write_text(json.dumps({'runId':os.getenv('GITHUB_RUN_ID'),'runAttempt':os.getenv('GITHUB_RUN_ATTEMPT'),'commit':os.getenv('GITHUB_SHA'),'repository':os.getenv('GITHUB_REPOSITORY'),'workflowRef':os.getenv('GITHUB_WORKFLOW_REF'),'files':rows,'formalArtifactAllowed':False,'deviceAcceptanceStatus':'pending'},indent=2)+'\n');print('Collected',len(rows),'files')
