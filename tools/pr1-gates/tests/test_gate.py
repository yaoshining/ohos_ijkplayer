import importlib.util,json,os,subprocess,sys,tempfile,unittest,shutil
from pathlib import Path
import yaml
HERE=Path(__file__).resolve().parent.parent
REPO=HERE.parents[1]
N=int(HERE.name[2])
def load():
 p=HERE/'engine.py'
 if not p.is_file():raise AssertionError('required real gate engine is absent')
 s=importlib.util.spec_from_file_location('gate_engine',p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
class Workflow(unittest.TestCase):
 def workflow(self,name):return yaml.load((REPO/'.github/workflows'/name).read_text(),Loader=yaml.BaseLoader)
 def test_real_target_events(self):
  names=['build-ffmpeg8.yml','phase17-mpv-repro.yml'] if N==1 else ['phase18-dependency-closure.yml','phase20-runtime-directories.yml']
  for name in names:
   with self.subTest(name=name):
    w=self.workflow(name);self.assertIn('pull_request',w['on']);self.assertIn('merge_group',w['on']);self.assertNotIn('pull_request_target',w['on']);self.assertEqual(w['permissions'],{'contents':'read'})
    paths=w['on']['pull_request'].get('paths',[])
    self.assertIn(f'tools/pr{N}-gates/**',paths);self.assertIn(f'specs/00{N+1}-pr{N}-ci-gates/**',paths);self.assertIn('.github/workflows/'+name,paths)
    for job in w['jobs'].values():
     self.assertNotIn('continue-on-error',job)
     for st in job['steps']:
      self.assertNotIn('continue-on-error',st)
      if st.get('uses','').startswith('actions/checkout@'):
       self.assertEqual(st.get('with',{}).get('fetch-depth'),'0');self.assertEqual(st.get('with',{}).get('persist-credentials'),'false');self.assertNotIn('ref',st.get('with',{}))
     runs='\n'.join(x.get('run','') for x in job['steps'])
     self.assertIn(f'tools/pr{N}-gates/snapshot.py begin',runs);self.assertIn(f'tools/pr{N}-gates/snapshot.py end',runs)
     self.assertNotIn('head_commit.message',job.get('if',''))
 def test_no_formal_publish(self):
  for p in (REPO/'.github/workflows').glob('*.yml'):
   if p.name in (['build-ffmpeg8.yml','phase17-mpv-repro.yml'] if N==1 else ['phase18-dependency-closure.yml','phase20-runtime-directories.yml']):
    self.assertNotIn('ohcodec-source-sdk-verified',p.read_text());self.assertNotIn('secrets.',p.read_text());self.assertNotIn('pull_request_target',p.read_text())
 def test_host_actual_runner(self):
  w=self.workflow(f'pr{N}-contracts.yml');self.assertIn('pull_request',w['on']);self.assertIn('merge_group',w['on'])
  runs='\n'.join(s.get('run','') for j in w['jobs'].values() for s in j['steps']);self.assertIn(f'python3 -B tools/pr{N}-gates/run.py',runs)
class Engine(unittest.TestCase):
 def setUp(self):
  self.e=load();self.t=tempfile.TemporaryDirectory();self.addCleanup(self.t.cleanup);self.root=Path(self.t.name);self.repo=self.root/'repo';self.repo.mkdir();self.git('init','-q');self.git('config','user.name','Test');self.git('config','user.email','test@example.invalid');(self.repo/'input').write_text('one');self.commit('base')
 def git(self,*args):return subprocess.check_output(['git','-C',str(self.repo),*args],stderr=subprocess.STDOUT).decode().strip()
 def commit(self,msg):self.git('add','.');self.git('commit','-qm',msg)
 def test_local_identity(self):
  x=self.e.identity(self.repo,{});self.assertEqual(x['testedHEAD'],self.git('rev-parse','HEAD'));self.assertTrue(x['exactCommitReplay'])
 def merge_env(self):
  basebranch=self.git('branch','--show-current');base=self.git('rev-parse','HEAD');self.git('checkout','-qb','feature');(self.repo/'feature').write_text('feature');self.commit('feature');head=self.git('rev-parse','HEAD');self.git('checkout','-q',basebranch);self.git('merge','--no-ff','-qm','merge','feature');event=self.root/'event.json';event.write_text(json.dumps({'pull_request':{'head':{'sha':head},'base':{'sha':base}}}));return {'GITHUB_ACTIONS':'true','GITHUB_EVENT_NAME':'pull_request','GITHUB_SHA':self.git('rev-parse','HEAD'),'GITHUB_EVENT_PATH':str(event)},head
 def test_real_pr_merge_identity(self):
  env,head=self.merge_env();x=self.e.identity(self.repo,env);self.assertEqual(x['pullRequestHead'],head);self.assertNotEqual(x['testedHEAD'],head);self.assertEqual(len(x['parents']),2)
 def test_mislabeled_pr_head_rejected(self):
  env,head=self.merge_env();env['GITHUB_SHA']=head
  with self.assertRaises(ValueError):self.e.identity(self.repo,env)
 def test_wrong_parent_rejected(self):
  env,_=self.merge_env();event=Path(env['GITHUB_EVENT_PATH']);x=json.loads(event.read_text());x['pull_request']['base']['sha']='a'*40;event.write_text(json.dumps(x))
  with self.assertRaises(ValueError):self.e.identity(self.repo,env)
 def test_dirty_requires_preview(self):
  (self.repo/'input').write_text('two')
  with self.assertRaises(ValueError):self.e.identity(self.repo,{})
  self.assertFalse(self.e.identity(self.repo,{},allow_dirty=True)['exactCommitReplay'])
 def test_real_subprocess_failure_not_swallowed(self):
  out=self.root/'failure';ok=self.e.execute(self.repo,out,[('bad',[sys.executable,'-c','print("actual FAIL");raise SystemExit(7)'])],{},timeout=3);self.assertFalse(ok);r=json.loads((out/'result.json').read_text());self.assertEqual(r['commands'][0]['returncode'],7);self.assertIn('actual FAIL',(out/'bad.log').read_text());self.assertTrue((out/'artifact-index.json').exists())
 def test_timeout_is_failure(self):
  out=self.root/'timeout';ok=self.e.execute(self.repo,out,[('hang',[sys.executable,'-c','import time;time.sleep(5)'])],{},timeout=.1);self.assertFalse(ok);self.assertTrue(json.loads((out/'result.json').read_text())['commands'][0]['timedOut'])
 def test_input_mutation_is_failure(self):
  out=self.root/'drift';ok=self.e.execute(self.repo,out,[('drift',[sys.executable,'-c','from pathlib import Path;Path("input").write_text("changed")'])],{});self.assertFalse(ok);self.assertFalse(json.loads((out/'result.json').read_text())['inputsUnchanged'])
 def test_normal_actual_command(self):
  out=self.root/'normal';self.assertTrue(self.e.execute(self.repo,out,[('ok',[sys.executable,'-c','print("actual PASS")'])],{}));self.assertTrue(json.loads((out/'result.json').read_text())['accepted'])
 def test_empty_commands_rejected(self):
  with self.assertRaises(ValueError):self.e.execute(self.repo,self.root/'empty',[],{})
 def test_collector_missing_and_boundary(self):
  p=self.root/'art';p.mkdir()
  with self.assertRaises(ValueError):self.e.collect(p)
  for name in ['identity.json','input-before.json','input-after.json','result.json']:(p/name).write_text('{}')
  (p/'escape.log').symlink_to(self.repo/'input')
  with self.assertRaises(ValueError):self.e.collect(p)
  (p/'escape.log').unlink();(p/'bad.log').write_bytes(b'\x00\xff')
  with self.assertRaises(ValueError):self.e.collect(p)
  (p/'bad.log').unlink();(p/'unexpected.hap').write_text('text pretending binary')
  with self.assertRaises(ValueError):self.e.collect(p)
 def test_full_cli_failure_cannot_become_green(self):
  folder=self.repo/'tools'/HERE.name;folder.mkdir(parents=True)
  for name in ['engine.py','run.py']:shutil.copyfile(HERE/name,folder/name)
  (folder/'commands.json').write_text(json.dumps({'commands':[{'name':'actual-failure','argv':['{python}','-c','print("FAIL_SENTINEL");raise SystemExit(9)']}]}));self.commit('runner')
  env={k:v for k,v in os.environ.items() if not k.startswith('GITHUB_')};out=self.root/'full-cli'
  result=subprocess.run([sys.executable,'-B',str(folder/'run.py'),'--out',str(out)],cwd=self.repo,env=env,capture_output=True,text=True)
  self.assertEqual(result.returncode,1,result.stdout+result.stderr);self.assertFalse(json.loads((out/'result.json').read_text())['accepted']);self.assertIn('FAIL_SENTINEL',(out/'actual-failure.log').read_text());self.assertTrue((out/'artifact-index.json').is_file())
 def test_snapshot_job_failure_remains_failure(self):
  folder=self.repo/'tools'/HERE.name;folder.mkdir(parents=True)
  for name in ['engine.py','snapshot.py']:shutil.copyfile(HERE/name,folder/name)
  self.commit('snapshot');env={k:v for k,v in os.environ.items() if not k.startswith('GITHUB_')};out=self.root/'snapshot'
  begin=subprocess.run([sys.executable,'-B',str(folder/'snapshot.py'),'begin','--out',str(out)],cwd=self.repo,env=env,capture_output=True,text=True);self.assertEqual(begin.returncode,0,begin.stderr)
  end=subprocess.run([sys.executable,'-B',str(folder/'snapshot.py'),'end','--out',str(out),'--job-status','failure'],cwd=self.repo,env=env,capture_output=True,text=True);self.assertEqual(end.returncode,1,end.stderr);self.assertFalse(json.loads((out/'result.json').read_text())['accepted'])
 def test_merge_group_wrong_base_rejected(self):
  env,_=self.merge_env();env['GITHUB_EVENT_NAME']='merge_group';Path(env['GITHUB_EVENT_PATH']).write_text(json.dumps({'merge_group':{'head_sha':env['GITHUB_SHA'],'base_sha':'a'*40}}))
  with self.assertRaises(ValueError):self.e.identity(self.repo,env)
 def test_ci_cannot_use_dirty_preview(self):
  (self.repo/'input').write_text('dirty')
  with self.assertRaises(ValueError):self.e.identity(self.repo,{'GITHUB_ACTIONS':'true','GITHUB_SHA':self.git('rev-parse','HEAD'),'GITHUB_EVENT_NAME':'push'},allow_dirty=True)
 def test_actual_head_drift_rejected(self):
  out=self.root/'head-drift';ok=self.e.execute(self.repo,out,[('commit',['git','commit','--allow-empty','-qm','drift'])],{});self.assertFalse(ok);self.assertFalse(json.loads((out/'result.json').read_text())['identityUnchanged'])
 def test_preflight_failure_has_structured_evidence(self):
  (self.repo/'input').write_text('dirty');out=self.root/'preflight';self.assertFalse(self.e.execute(self.repo,out,[('ok',[sys.executable,'-c','print("never")'])],{}));self.assertFalse(json.loads((out/'result.json').read_text())['accepted']);self.assertIn('captureError',json.loads((out/'identity.json').read_text()));self.assertTrue((out/'artifact'/'artifact-index.json').is_file())
 def test_real_zero_unittest_rejected(self):
  empty=self.repo/'empty-tests';empty.mkdir();out=self.root/'zero-tests';ok=self.e.execute(self.repo,out,[('zero',[sys.executable,'-B','-m','unittest','discover','-s',str(empty),'-v'])],{});self.assertFalse(ok);row=json.loads((out/'result.json').read_text())['commands'][0];self.assertEqual(row['returncode'],0);self.assertEqual(row['testsRun'],0)
 def test_stale_collection_index_removed_on_failure(self):
  out=self.root/'stale';self.assertTrue(self.e.execute(self.repo,out,[('ok',[sys.executable,'-c','print("pass")'])],{}));(out/'bad.log').write_bytes(b'\x00')
  with self.assertRaises(ValueError):self.e.collect(out)
  self.assertFalse((out/'artifact-index.json').exists());self.assertFalse((out/'artifact').exists())
 def test_merge_group_identity(self):
  env,_=self.merge_env();env['GITHUB_EVENT_NAME']='merge_group';Path(env['GITHUB_EVENT_PATH']).write_text(json.dumps({'merge_group':{'head_sha':env['GITHUB_SHA'],'base_sha':self.git('rev-parse','HEAD^')}}));self.assertEqual(self.e.identity(self.repo,env)['event'],'merge_group')
if __name__=='__main__':unittest.main()
