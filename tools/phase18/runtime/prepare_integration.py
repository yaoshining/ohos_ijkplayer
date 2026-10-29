from pathlib import Path
import json,shutil,sys
from input_gate import sha,inventory,require_fresh
R=Path(__file__).resolve().parents[1];base=Path(sys.argv[1]).resolve();P=require_fresh(R/'integration/input-package');P.mkdir(parents=True)
for sub in ['sources','ffmpeg','baseline']:shutil.copytree(base/sub,P/sub)
(P/'deps/lib/pkgconfig').mkdir(parents=True);(P/'deps/include').mkdir();origins=[]
names=['libass.a','libfontconfig.a','libfreetype.a','libfribidi.a','libharfbuzz.a','liblcms2.a','liblua.a','libxml2.a','libshaderc_combined.a','libdovi.a']
for root in [R/'runs/native-01/prefix',R/'runs/shaderc-01/prefix',R/'runs/dovi-01/install/usr/local']:
 for src in sorted(root.rglob('*')):
  if not src.is_file():continue
  rel=src.relative_to(root)
  if rel.parts[0]!='include' and src.name not in names and not (src.suffix=='.pc' and src.stem in ['libass','fontconfig','freetype2','fribidi','harfbuzz','lcms2','lua','libxml-2.0','shaderc','dovi']):continue
  dst=P/'deps'/rel;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(src,dst)
  if dst.suffix=='.pc':dst.write_text(dst.read_text().replace('prefix=/usr/local','prefix=${pcfiledir}/../..'))
  origins.append({'source':str(src),'sourceSHA256':sha(src),'packagePath':str(dst.relative_to(P)),'packageSHA256':sha(dst)})
assert sorted(x.name for x in (P/'deps/lib').glob('*.a'))==sorted(names)
(P/'provenance').mkdir();(P/'provenance/new-dependencies.json').write_text(json.dumps(origins,indent=2)+'\n')
relocations=json.loads((base/'relocations.json').read_text());m={'schemaVersion':1,'files':inventory(P),'relocations':relocations,'cachedDependenciesRebuilt':True,'formalArtifactAllowed':False,'deviceAcceptanceStatus':'pending'};(P/'package.json').write_text(json.dumps(m,indent=2)+'\n');print('New CI integration package',len(m['files']))
