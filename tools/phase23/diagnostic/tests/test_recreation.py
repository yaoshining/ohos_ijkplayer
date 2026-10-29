from pathlib import Path
import subprocess,tempfile,unittest,shutil
R=Path(__file__).resolve().parents[1]
class Recreation(unittest.TestCase):
 def test_cancel_during_probe_and_remount_wait(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d);shutil.copyfile(R/'RecreationGuard.ts',p/'RecreationGuard.ts');(p/'test.mjs').write_text('''import assert from 'node:assert/strict';import { RecreationGuard } from './RecreationGuard.ts';
for(const where of ['probe','delay','none']){let doneProbe,doneDelay;const probe=new Promise(r=>doneProbe=r),delay=new Promise(r=>doneDelay=r);let hidden=0,mounted=0;const g=new RecreationGuard();g.begin();const work=g.perform(()=>probe,()=>hidden++,()=>mounted++,()=>delay);if(where==='probe')g.cancel();doneProbe();await Promise.resolve();await Promise.resolve();if(where==='delay')g.cancel();doneDelay();await work;assert.equal(hidden,where==='probe'?0:1);assert.equal(mounted,where==='none'?1:0);}
''');subprocess.run(['node','--experimental-strip-types',str(p/'test.mjs')],check=True)
