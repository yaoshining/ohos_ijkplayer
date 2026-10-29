from pathlib import Path
import hashlib,json,os,shutil
out=Path('out/phase22-contract');out.mkdir(parents=True,exist_ok=True);shutil.copytree('tools/phase22',out/'source');(out/'identity.json').write_text(json.dumps({'commit':os.environ['GITHUB_SHA'],'runId':os.environ['GITHUB_RUN_ID'],'jobStatus':os.environ['JOB_STATUS'],'scope':'host contract regression only','targetExecuted':False}))
files=[{'path':str(p.relative_to(out)),'size':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in sorted(out.rglob('*')) if p.is_file()];(out/'evidence-index.json').write_text(json.dumps({'files':files},indent=2)+'\n')
