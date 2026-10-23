import importlib.util,json,sys,tempfile,unittest
from pathlib import Path
s=importlib.util.spec_from_file_location('gate',Path(__file__).with_name('gate.py'));g=importlib.util.module_from_spec(s);s.loader.exec_module(g)
class GateTests(unittest.TestCase):
 def test_success(self):
  self.assertTrue(g.execute([sys.executable,'-c','print("ok")'],Path.cwd(),2)['passed'])
 def test_failure(self):
  self.assertFalse(g.execute([sys.executable,'-c','raise SystemExit(9)'],Path.cwd(),2)['passed'])
 def test_timeout(self):
  self.assertFalse(g.execute([sys.executable,'-c','import time;time.sleep(2)'],Path.cwd(),.05)['passed'])
 def test_missing_tool(self):
  self.assertFalse(g.execute(['/does-not-exist'],Path.cwd(),2)['passed'])
 def test_zero_tests(self):
  self.assertFalse(g.unittest_ok('Ran 0 tests in 0s\nOK\n'))
 def test_tests(self):
  self.assertTrue(g.unittest_ok('Ran 3 tests in 0s\nOK\n'))
 def test_index(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d);(p/'a.json').write_text('{}');rows=[{'path':'a.json','size':2,'sha256':g.sha(p/'a.json')}];(p/'artifact-index.json').write_text(json.dumps({'files':rows}));g.verify_artifact(p)
   (p/'a.json').write_text('bad')
   with self.assertRaises(ValueError):g.verify_artifact(p)
 def test_missing_evidence(self):
  with tempfile.TemporaryDirectory() as d:
   with self.assertRaises(ValueError):g.verify_artifact(Path(d))
 def test_incomplete_matrix(self):
  self.assertFalse(g.aggregate([{'case':'21','accepted':True}]))
 def test_complete_matrix(self):
  self.assertTrue(g.aggregate([{'case':c,'accepted':True} for c in g.CASES]))
 def test_duplicate_matrix(self):
  self.assertFalse(g.aggregate([{'case':c,'accepted':True} for c in g.CASES]+[{'case':'21','accepted':True}]))
if __name__=='__main__':unittest.main()
