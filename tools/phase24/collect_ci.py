from pathlib import Path
import hashlib,json,os,shutil
root=Path('tools/phase24');out=Path('out/phase24-contract');out.mkdir(parents=True,exist_ok=True)
shutil.copytree(root,out/'source',dirs_exist_ok=True)
shutil.copytree('specs/001-ffmpeg-ohcodec-producer/phase24',out/'spec',dirs_exist_ok=True)
(out/'identity.json').write_text(json.dumps({'commit':os.environ.get('GITHUB_SHA'),'runId':os.environ.get('GITHUB_RUN_ID'),'jobStatus':os.environ.get('JOB_STATUS'),'scope':'host diagnostic contracts only','targetExecutedByCI':False,'NASLongPlaybackAccepted':False,'HDRComplete':False,'formalArtifactAllowed':False},indent=2)+'\n')
rows=[{'path':str(p.relative_to(out)),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in sorted(out.rglob('*')) if p.is_file() and p.name!='evidence-index.json']
(out/'evidence-index.json').write_text(json.dumps({'files':rows},indent=2)+'\n')
