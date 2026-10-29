from pathlib import Path
import subprocess,tempfile,unittest,shutil
R=Path(__file__).resolve().parents[1]
class Lifecycle(unittest.TestCase):
 def test_cancel_prevents_continuation_and_stale_generation(self):
  with tempfile.TemporaryDirectory() as t:
   p=Path(t);shutil.copyfile(R/'RunGate.ts',p/'RunGate.ts')
   (p/'test.mjs').write_text('''import assert from 'node:assert/strict';import { RunGate } from './RunGate.ts';
+const g=new RunGate();const token=g.begin();assert(g.accepts(token,true));assert(!g.accepts(token,false));let calls=0;
+async function flow(){for(let i=0;i<3;i++){if(!g.accepts(token,true))return;calls++;await Promise.resolve();if(!g.accepts(token,true))return;}}
+const pending=flow();g.cancel();await pending;assert.equal(calls,1);assert(!g.accepts(token,true));const next=g.begin();assert(g.accepts(next,true));assert(!g.accepts(token,true));g.cancel();g.cancel();assert(!g.accepts(next,true));
+'''.replace('\n+','\n'));subprocess.run(['node','--experimental-strip-types',str(p/'test.mjs')],check=True)
