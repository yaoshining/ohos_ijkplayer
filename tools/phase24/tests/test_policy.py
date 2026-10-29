import pathlib,subprocess,tempfile,unittest
ROOT=pathlib.Path(__file__).resolve().parents[1]
class PolicyTests(unittest.TestCase):
 def test_real_native_policy(self):
  with tempfile.TemporaryDirectory() as d:
   binary=pathlib.Path(d)/'policy'
   r=subprocess.run(['c++','-std=c++17','-I'+str(ROOT/'app/entry/src/main/cpp'),str(ROOT/'tests/policy_test.cpp'),'-o',str(binary)],capture_output=True,text=True)
   self.assertEqual(r.returncode,0,r.stderr)
   r=subprocess.run([str(binary)],capture_output=True,text=True)
   self.assertEqual(r.returncode,0,r.stderr)
