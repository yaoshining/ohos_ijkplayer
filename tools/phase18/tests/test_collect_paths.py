from pathlib import Path
import json,os,shutil,subprocess,sys,tempfile,unittest
HERE=Path(__file__).resolve().parents[1]
class CollectorPaths(unittest.TestCase):
 def exercise(self,folder):
  t=tempfile.TemporaryDirectory();self.addCleanup(t.cleanup);repo=Path(t.name)/folder;tools=repo/'tools/phase18';tools.mkdir(parents=True)
  for name in ['collect.py','evidence_contract.py']:shutil.copyfile(HERE/name,tools/name)
  wf=repo/'.github/workflows/phase18-dependency-closure.yml';wf.parent.mkdir(parents=True);wf.write_text('fixture')
  root=repo/'out/phase18-ci';expected=['runs/native-01/prefix/lib/libass.a','integration/runs/origin-a/mpv/build/config.h','integration/runs/origin-a/install/usr/local/lib/libmpv.so','integration/runs/origin-a/validation/static-validation.json','locks/tools-before.json']
  for name in expected+['runs/native-01/home/unrelated.json','runs/native-01/source/unrelated.h']:
   p=root/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_text('{}')
  pr=subprocess.run([sys.executable,'-B',str(tools/'collect.py')],env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1'},capture_output=True,text=True);self.assertEqual(pr.returncode,0,pr.stderr)
  result=repo/'out/phase18-artifact';index=json.loads((result/'evidence-index.json').read_text());paths={x['path'] for x in index['files']}
  for p in expected:self.assertIn(p,paths)
  self.assertNotIn('runs/native-01/home/unrelated.json',paths);self.assertNotIn('runs/native-01/source/unrelated.h',paths)
 def test_absolute_home_does_not_exclude_all_evidence(self):self.exercise('home/runner/work/project')
 def test_actual_run_home_and_source_still_excluded(self):self.exercise('ordinary/project')
 def test_success_marker_requires_real_build_evidence(self):
  with tempfile.TemporaryDirectory() as t:
   repo=Path(t);tools=repo/'tools/phase18';tools.mkdir(parents=True)
   for name in ['collect.py','evidence_contract.py']:shutil.copyfile(HERE/name,tools/name)
   wf=repo/'.github/workflows/phase18-dependency-closure.yml';wf.parent.mkdir(parents=True);wf.write_text('fixture')
   r=repo/'out/phase18-ci';r.mkdir(parents=True);(r/'phase18-verification.json').write_text('{"allPassed":true}')
   pr=subprocess.run([sys.executable,'-B',str(tools/'collect.py')],env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1'},capture_output=True,text=True)
   self.assertNotEqual(pr.returncode,0,'success marker without archive/run evidence must not be accepted')
