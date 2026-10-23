import importlib.util,json,sys,tempfile,unittest,os,subprocess
from unittest.mock import patch
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
   p=Path(d).resolve();(p/'a.json').write_text('{}');rows=[{'path':'a.json','size':2,'sha256':g.sha(p/'a.json')}];(p/'artifact-index.json').write_text(json.dumps({'files':rows}));g.verify_artifact(p)
   (p/'a.json').write_text('bad')
   with self.assertRaises(ValueError):g.verify_artifact(p)
 def test_missing_evidence(self):
  with tempfile.TemporaryDirectory() as d:
   with self.assertRaises(ValueError):g.verify_artifact(Path(d).resolve())
 def test_incomplete_matrix(self):
  self.assertFalse(g.aggregate([{'case':'21','accepted':True}]))
 def test_complete_matrix(self):
  self.assertTrue(g.aggregate([{'case':c,'accepted':True} for c in g.CASES]))
 def test_duplicate_matrix(self):
  self.assertFalse(g.aggregate([{'case':c,'accepted':True} for c in g.CASES]+[{'case':'21','accepted':True}]))
class IdentityTests(unittest.TestCase):
 def test_real_merge_identity(self):
  with tempfile.TemporaryDirectory() as d:
   repo=Path(d).resolve()/'repo';repo.mkdir()
   def git(*args):return subprocess.check_output(['git','-C',str(repo),'-c','user.name=Test','-c','user.email=test@example.invalid',*args],stderr=subprocess.DEVNULL,text=True).strip()
   git('init','-b','main');(repo/'a').write_text('a');git('add','.');git('commit','-m','base');base=git('rev-parse','HEAD');git('checkout','-b','topic');(repo/'b').write_text('b');git('add','.');git('commit','-m','head');head=git('rev-parse','HEAD');git('checkout','--detach',base);git('merge','--no-ff',head,'-m','merge');merge=git('rev-parse','HEAD')
   event=Path(d).resolve()/'event.json'
   def ev(b,h):event.write_text(json.dumps({'number':9,'pull_request':{'base':{'sha':b},'head':{'sha':h}}}))
   env={'GITHUB_ACTIONS':'true','GITHUB_EVENT_NAME':'pull_request','GITHUB_EVENT_PATH':str(event),'GITHUB_SHA':merge}
   with patch.object(g,'ROOT',repo),patch.dict(os.environ,env):
    ev(base,head);self.assertEqual(g.identity()['checkout'],merge)
    ev(head,base)
    with self.assertRaises(ValueError):g.identity()
    ev(base,head)
    with patch.dict(os.environ,{'GITHUB_SHA':head}):
     with self.assertRaises(ValueError):g.identity()
    (repo/'dirty').write_text('x')
    with self.assertRaises(ValueError):g.identity()
    (repo/'dirty').unlink()
    with patch.dict(os.environ,{'GITHUB_EVENT_NAME':'workflow_dispatch'}):self.assertEqual(g.identity()['checkout'],merge)
    git('checkout','--detach',head)
    with patch.dict(os.environ,{'GITHUB_SHA':head}):
     with self.assertRaises(ValueError):g.identity()
class CollectionTests(unittest.TestCase):
 def test_reject_binary_and_symlink(self):
  for raw in (b'\x7fELF\x00',b'\xff'):
   with tempfile.TemporaryDirectory() as d:
    p=Path(d).resolve()/'x.log';p.write_bytes(raw)
    with self.assertRaises(ValueError):g.text_bytes(p)
  with tempfile.TemporaryDirectory() as d:
   root=Path(d).resolve();(root/'real').mkdir();(root/'real/x.log').write_text('x');(root/'link').symlink_to(root/'real',target_is_directory=True)
   with self.assertRaises(ValueError):g.text_bytes(root/'link/x.log')
 def test_workflow_complete(self):
  self.assertTrue(g.workflow_valid(g.ROOT/'.github/workflows/pr3-contracts.yml'))
 def test_old_workflows_rejected(self):
  self.assertFalse(g.workflow_valid(g.ROOT/'.github/workflows/phase31-normal-validation.yml'))
 def test_workflow_missing_case_rejected(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d).resolve()/'x.yml';p.write_text((g.ROOT/'.github/workflows/pr3-contracts.yml').read_text().replace("'31'",''))
   self.assertFalse(g.workflow_valid(p))
if __name__=='__main__':unittest.main()
