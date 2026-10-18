from pathlib import Path
import json,subprocess,shutil
from input_gate import sha,inventory,verify_tree,safe_extract,require_fresh
R=Path(__file__).resolve().parents[1];P=require_fresh(R/'source-package');P.mkdir();(P/'archives').mkdir();(P/'source').mkdir()
records=[]
def export(name,repo,commit,dest=None):
 archive=P/'archives'/(name+'.tar');argv=['git','--no-optional-locks','-c','core.fsmonitor=false','-C',repo,'archive','--format=tar','--output='+str(archive),commit]
 subprocess.run(argv,check=True);dest=dest or P/'source'/name
 if dest.is_dir() and not any(dest.iterdir()):dest.rmdir()
 safe_extract(archive,dest)
 records.append({'name':name,'originRepository':repo,'commit':commit,'archive':str(archive.relative_to(P)),'archiveSHA256':sha(archive),'exportArgv':argv,'exportedFiles':inventory(dest)})
native=json.loads((R/'research/native/recipe.json').read_text())
for c in native['components']:
 if c['component']=='lua':
  archive=P/'archives/lua-5.2.4.tar.gz';shutil.copyfile(c['sourceArchive'],archive);assert sha(archive)==c['sourceArchiveSHA256']
  tmp=safe_extract(archive,P/'lua-extract');shutil.move(tmp/'lua-5.2.4',P/'source/lua');tmp.rmdir();records.append({'name':'lua','archive':str(archive.relative_to(P)),'archiveSHA256':sha(archive),'exportedFiles':inventory(P/'source/lua')})
 else:export(c['component'],c['repository'],c['commit'])
shader=json.loads((R/'research/shaderc/recipe.json').read_text())
for c in shader['components']:export(c['name'],c['readOnlyRepository'],c['commit'],P/'source/shaderc'/c['extractRelative'])
cache=Path('/Users/yaoshining/.cache/vidall-player/libmpv-ohos-build/libmpv')
export('dovi',str(cache/'dovi_tools'),'b25558062e4a56973482ec70133bd7b891320e48')
rows=inventory(P/'source');verify_tree(P/'source',rows,source=True)
(P/'source-original.json').write_text(json.dumps(rows,indent=2)+'\n');(P/'source-origins.json').write_text(json.dumps(records,indent=2)+'\n')
print('Exported',len(records),'source roots;',len(rows),'files')
