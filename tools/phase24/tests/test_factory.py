import pathlib,subprocess,tempfile,unittest
ROOT=pathlib.Path(__file__).resolve().parents[1];CPP=ROOT/'app/entry/src/main/cpp'
class FactoryTests(unittest.TestCase):
 def test_real_factory_private_options_and_rgb10(self):
  with tempfile.TemporaryDirectory() as d:
   binary=pathlib.Path(d)/'test'
   r=subprocess.run(['c++','-std=c++17','-I'+str(CPP),'-I'+str(CPP/'include'),str(ROOT/'tests/factory_test.cpp'),str(CPP/'play_factory.cpp'),'-o',str(binary)],capture_output=True,text=True)
   self.assertEqual(r.returncode,0,r.stderr)
   r=subprocess.run([str(binary)],capture_output=True,text=True);self.assertEqual(r.returncode,0,r.stderr)
