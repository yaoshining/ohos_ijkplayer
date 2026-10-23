from pathlib import Path
import json,shutil
from input_gate import sha,inventory,verify_tree,require_fresh
R=Path(__file__).resolve().parents[1];research=R/'research/dovi';B=require_fresh(R/'dovi-input');B.mkdir()
for sub in ['toolchain','tools','archives']:(B/sub).mkdir()
shutil.copytree(R/'source-package/source/dovi',B/'source');shutil.copytree(research/'vendor',B/'vendor')
locks=json.loads((research/'toolchain-pins.json').read_text());root=Path(locks['observedRoot']);copies=[]
for row in locks['files']:
 src=Path(row['path']);assert sha(src)==row['sha256']
 if src.is_relative_to(root):dest=B/'toolchain'/src.relative_to(root)
 elif src.name.startswith('cargo-c'):dest=B/'tools'/src.name
 else:continue
 dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,dest);assert sha(dest)==row['sha256'];copies.append({'from':str(src),'to':str(dest.relative_to(B)),'sha256':row['sha256']})
for c in json.loads((research/'crate-pins.json').read_text())['crates']:
 src=Path(c['archive']['path']);assert sha(src)==c['checksum'];dest=B/'archives'/src.name;shutil.copyfile(src,dest)
(B/'copy-binding.json').write_text(json.dumps(copies,indent=2)+'\n')
rows=inventory(B);(R/'locks/dovi-input.json').write_text(json.dumps({'root':str(B),'files':rows,'compilerStdRebuilt':False,'hostOSBoundary':'macOS dyld system libraries; observed OS build and loader dependencies bound separately'},indent=2)+'\n')
print('Dovi input:',len(rows),'files')
