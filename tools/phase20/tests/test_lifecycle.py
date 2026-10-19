from pathlib import Path
import subprocess,tempfile,unittest
R=Path(__file__).resolve().parents[1]
class Lifecycle(unittest.TestCase):
 def test_actual_wrapper_with_controlled_backend(self):
  with tempfile.TemporaryDirectory() as t:
   exe=Path(t)/'lifecycle'
   subprocess.run(['cc','-pthread','-Wall','-Wextra','-Werror','-I',str(R/'runtime'),str(R/'tests/lifecycle.c'),str(R/'runtime/smb_runtime.c'),'-o',str(exe)],check=True)
   for case in ['pending','failures','repeat','reentry','threads']:
    with self.subTest(case=case):subprocess.run([str(exe),case],check=True,timeout=15)
   base=Path(t).resolve();config=base/'smb.conf';config.write_text('[global]\n');state=base/'state';cache=base/'cache';resource=base/'resource'
   for p in [state,cache,resource,state/'private',state/'state',state/'lock']:p.mkdir()
   for repeat in range(30):
    with self.subTest(race=repeat):subprocess.run([str(exe),'create-config-race',str(config),str(state),str(cache),str(resource)],check=True,timeout=15)
