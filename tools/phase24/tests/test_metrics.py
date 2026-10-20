import pathlib,subprocess,tempfile,unittest
ROOT=pathlib.Path(__file__).resolve().parents[1];CPP=ROOT/'app/entry/src/main/cpp'
class MetricsTests(unittest.TestCase):
 def test_actual_typed_query(self):
  with tempfile.TemporaryDirectory() as d:
   b=pathlib.Path(d)/'test';r=subprocess.run(['c++','-std=c++17','-I'+str(CPP),'-I'+str(CPP/'include'),str(ROOT/'tests/metrics_test.cpp'),'-o',str(b)],capture_output=True,text=True);self.assertEqual(r.returncode,0,r.stderr)
   r=subprocess.run([str(b)],capture_output=True,text=True);self.assertEqual(r.returncode,0,r.stderr)
