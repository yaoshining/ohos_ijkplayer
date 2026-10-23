from pathlib import Path
import json,hashlib,shutil,os,platform
repo=Path(__file__).resolve().parents[2];src=repo/'out/phase17-ci';dest=repo/'out/phase17-ci-artifacts';dest.mkdir(parents=True,exist_ok=False)
for p in sorted(src.rglob('*')):
 if not p.is_file():continue
 rel=p.relative_to(src)
 if any(part in ['input-package','target-overlay','sdk','unpacked','deps','ffmpeg','source','host-cache','package-cache','tmp']for part in rel.parts):continue
 keep=p.suffix in ['.json','.log','.txt','.ini','.md','.h'] or (p.name=='libmpv.so'and 'install'in rel.parts)or p.name=='install-unstripped.so'or(p.name=='libplacebo.a'and'install'in rel.parts)or p.name=='link.map'
 if not keep:continue
 q=dest/rel;q.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,q)
host=repo/'out/phase17-host-tools/binding.json'
if host.is_file():shutil.copyfile(host,dest/'host-ninja-binding.json')
(dest/'run-identity.json').write_text(json.dumps({'runUrl':os.environ['GITHUB_SERVER_URL']+'/'+os.environ['GITHUB_REPOSITORY']+'/actions/runs/'+os.environ['GITHUB_RUN_ID'],'commit':os.environ['GITHUB_SHA'],'platform':platform.platform(),'actualCoverageMustComeFromSuccessfulCommands':True,'formalArtifactAllowed':False},indent=2)+'\n')
files=[{'path':str(p.relative_to(dest)),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'sizeBytes':p.stat().st_size}for p in sorted(dest.rglob('*'))if p.is_file()];(dest/'artifact-index.json').write_text(json.dumps({'files':files},indent=2)+'\n');print('artifact files',len(files))
