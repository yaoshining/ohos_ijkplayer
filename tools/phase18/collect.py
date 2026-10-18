from pathlib import Path
import os,json,hashlib,shutil,subprocess
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
rows=[]
for p in sorted(set(selected)):
 dest=D/p.relative_to(R);dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,dest);rows.append({'path':str(dest.relative_to(D)),'size':dest.stat().st_size,'sha256':hashlib.sha256(dest.read_bytes()).hexdigest()})
(D/'evidence-index.json').write_text(json.dumps({'runId':os.getenv('GITHUB_RUN_ID'),'commit':os.getenv('GITHUB_SHA'),'files':rows,'formalArtifactAllowed':False,'deviceAcceptanceStatus':'pending'},indent=2)+'\n');print('Collected',len(rows),'files')
