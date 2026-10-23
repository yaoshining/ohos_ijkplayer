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
class AggregateCLITests(unittest.TestCase):
 def test_missing_and_foreign_identity_fail_closed(self):
  with tempfile.TemporaryDirectory() as d:
   root=Path(d).resolve();matrix=root/'matrix';matrix.mkdir()
   for c in g.CASES:
    case=matrix/c;case.mkdir();g.write(case/'result.json',{'case':c,'accepted':True,'identity':{'checkout':'wrong'}});g.write(case/'artifact-index.json',{'files':[{'path':'result.json','size':(case/'result.json').stat().st_size,'sha256':g.sha(case/'result.json')}]})
   p=subprocess.run([sys.executable,'-B',str(g.ROOT/'tools/pr3-gates/gate.py'),'--aggregate',str(matrix),'--out',str(root/'result.json')],capture_output=True)
   self.assertNotEqual(p.returncode,0)
class FullAggregateCLITests(unittest.TestCase):
 def test_all_indexes_checked(self):
  import shutil
  with tempfile.TemporaryDirectory() as d:
   root=Path(d).resolve();repo=root/'repo';(repo/'tools/pr3-gates').mkdir(parents=True);(repo/'.github/workflows').mkdir(parents=True)
   shutil.copy(g.ROOT/'tools/pr3-gates/gate.py',repo/'tools/pr3-gates/gate.py');shutil.copy(g.ROOT/'.github/workflows/pr3-contracts.yml',repo/'.github/workflows/pr3-contracts.yml')
   def git(*a):return subprocess.check_output(['git','-C',str(repo),'-c','user.name=Test','-c','user.email=test@example.invalid',*a],stderr=subprocess.DEVNULL,text=True).strip()
   git('init','-b','main');git('add','.');git('commit','-m','test')
   ident={'checkout':git('rev-parse','HEAD'),'tree':git('rev-parse','HEAD^{tree}'),'parents':'','status':'','event':'local'}
   matrix=root/'matrix';matrix.mkdir()
   for c in g.CASES:
    case=matrix/c;case.mkdir();g.write(case/'result.json',{'case':c,'accepted':True,'identity':ident});(case/'log.txt').write_text('ok');g.write(case/'artifact-index.json',{'files':[{'path':p.name,'size':p.stat().st_size,'sha256':g.sha(p)} for p in case.iterdir()]})
   env={k:v for k,v in os.environ.items() if not k.startswith('GITHUB_')}
   def run():return subprocess.run([sys.executable,'-B',str(repo/'tools/pr3-gates/gate.py'),'--aggregate',str(matrix),'--out',str(root/'result.json')],env=env,capture_output=True).returncode
   self.assertEqual(run(),0)
   for c in ('22','31'):
    (matrix/c/'log.txt').write_text('bad');self.assertNotEqual(run(),0);(matrix/c/'log.txt').write_text('ok')
class IdentityTests(unittest.TestCase):
 def test_real_merge_identity(self):
  with tempfile.TemporaryDirectory() as d:
   repo=Path(d).resolve()/'repo';repo.mkdir()
   def git(*args):return subprocess.check_output(['git','-C',str(repo),'-c','user.name=Test','-c','user.email=test@example.invalid',*args],stderr=subprocess.DEVNULL,text=True).strip()
   git('init','-b','main');(repo/'a').write_text('a');git('add','.');git('commit','-m','base');base=git('rev-parse','HEAD');git('checkout','-b','topic');(repo/'b').write_text('b');git('add','.');git('commit','-m','head');head=git('rev-parse','HEAD');git('checkout','--detach',base);git('merge','--no-ff',head,'-m','merge');merge=git('rev-parse','HEAD')
   event=Path(d).resolve()/'event.json'
   def ev(b,h):event.write_text(json.dumps({'number':9,'pull_request':{'base':{'sha':b,'ref':'main'},'head':{'sha':h}}}))
   env={'GITHUB_ACTIONS':'true','GITHUB_EVENT_NAME':'pull_request','GITHUB_EVENT_PATH':str(event),'GITHUB_SHA':merge,'GITHUB_REF':'refs/pull/9/merge','GITHUB_BASE_REF':'main'}
   with patch.object(g,'ROOT',repo),patch.dict(os.environ,env):
    ev(base,head);self.assertEqual(g.identity()['checkout'],merge)
    shallow=Path(d).resolve()/'shallow'
    subprocess.run(['git','clone','--depth=1',repo.as_uri(),str(shallow)],check=True,capture_output=True)
    with patch.object(g,'ROOT',shallow):
     with self.assertRaises(ValueError):g.identity()
     subprocess.run(['git','-C',str(shallow),'fetch','--unshallow'],check=True,capture_output=True)
     self.assertEqual(g.identity()['checkout'],merge)

    with patch.dict(os.environ,{'GITHUB_EVENT_NAME':'merge_group'}):
     event.write_text(json.dumps({'merge_group':{'base_sha':base,'head_sha':merge}}));self.assertEqual(g.identity()['checkout'],merge)
     event.write_text(json.dumps({'merge_group':{'base_sha':base,'head_sha':head}}))
     with self.assertRaises(ValueError):g.identity()
     event.write_text(json.dumps({'merge_group':{'base_sha':'0'*40,'head_sha':merge}}))
     with self.assertRaises(ValueError):g.identity()
    ev(base,head)

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
class AdvancedBaseTests(unittest.TestCase):
 def test_event_base_can_lag_actual_merge_base(self):
  with tempfile.TemporaryDirectory() as d:
   repo=Path(d).resolve()/'repo';repo.mkdir()
   def git(*args):return subprocess.check_output(['git','-C',str(repo),'-c','user.name=Test','-c','user.email=test@example.invalid',*args],stderr=subprocess.DEVNULL,text=True).strip()
   git('init','-b','main');(repo/'a').write_text('a');git('add','.');git('commit','-m','base');declared=git('rev-parse','HEAD')
   git('checkout','-b','topic');(repo/'feature').write_text('feature');git('add','.');git('commit','-m','feature');head=git('rev-parse','HEAD')
   git('checkout','main');(repo/'advance').write_text('advance');git('add','.');git('commit','-m','advance');actual=git('rev-parse','HEAD');git('merge','--no-ff',head,'-m','merge');merge=git('rev-parse','HEAD')
   event=Path(d).resolve()/'event.json'
   def ev(base,topic):event.write_text(json.dumps({'number':9,'pull_request':{'base':{'sha':base,'ref':'main'},'head':{'sha':topic}}}))
   ev(declared,head)
   env={'GITHUB_ACTIONS':'true','GITHUB_EVENT_NAME':'pull_request','GITHUB_EVENT_PATH':str(event),'GITHUB_SHA':merge,'GITHUB_REF':'refs/pull/9/merge','GITHUB_BASE_REF':'main'}
   with patch.object(g,'ROOT',repo),patch.dict(os.environ,env):
    identity=g.identity();self.assertEqual(identity['prBase'],declared);self.assertEqual(identity['actualMergeBase'],actual)
    for bad in ({'GITHUB_REF':'refs/pull/8/merge'},{'GITHUB_BASE_REF':'other'},{'GITHUB_SHA':head}):
     with patch.dict(os.environ,bad):
      with self.assertRaises(ValueError):g.identity()
    ev(head,head)
    with self.assertRaises(ValueError):g.identity()
    ev(declared,declared)
    with self.assertRaises(ValueError):g.identity()
    ev('0'*40,head)
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
