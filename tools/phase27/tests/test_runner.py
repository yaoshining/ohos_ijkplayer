import importlib.util,json,hashlib,tempfile,unittest
from pathlib import Path
spec=importlib.util.spec_from_file_location('runner',Path(__file__).parents[1]/'runner.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
class Gates(unittest.TestCase):
 def fixture(self,p,name='source/a.c'):
  f=p/name;f.parent.mkdir(parents=True,exist_ok=True);f.write_text('source\n');r={'path':name,'size':7,'sha256':hashlib.sha256(f.read_bytes()).hexdigest()};(p/'source-index.json').write_text(json.dumps([r]));return f
 def test_valid_source(self):
  with tempfile.TemporaryDirectory()as t:p=Path(t);self.fixture(p);self.assertEqual(len(m.verify(p)),1)
 def test_changed_source(self):
  with tempfile.TemporaryDirectory()as t:p=Path(t);f=self.fixture(p);f.write_text('changed');self.assertRaises(ValueError,m.verify,p)
 def test_path_traversal(self):
  with tempfile.TemporaryDirectory()as t:p=Path(t);(p/'source-index.json').write_text('[{"path":"../secret"}]');self.assertRaises(ValueError,m.verify,p)
 def test_forbidden_binary(self):
  with tempfile.TemporaryDirectory()as t:p=Path(t);self.fixture(p,'source/lib.so');self.assertRaises(ValueError,m.verify,p)
 def test_symlink(self):
  with tempfile.TemporaryDirectory()as t:p=Path(t);f=self.fixture(p);f.unlink();f.symlink_to('/etc/hosts');self.assertRaises(ValueError,m.verify,p)
 def test_duplicate(self):
  with tempfile.TemporaryDirectory()as t:p=Path(t);self.fixture(p);r=json.loads((p/'source-index.json').read_text());(p/'source-index.json').write_text(json.dumps(r+r));self.assertRaises(ValueError,m.verify,p)
 def test_extra_source(self):
  with tempfile.TemporaryDirectory()as t:p=Path(t);self.fixture(p);(p/'source/extra.c').write_text('extra');self.assertRaises(ValueError,m.verify,p)
 def test_artifact_rejects_binary(self):
  with tempfile.TemporaryDirectory()as t:p=Path(t);(p/'library.so').write_bytes(b'ELF');self.assertRaises(ValueError,m.artifact_audit,p)
 def test_artifact_includes_hidden_workflow(self):
  with tempfile.TemporaryDirectory()as t:
   p=Path(t);f=p/'execution/.github/workflows/phase27.yml';f.parent.mkdir(parents=True);f.write_text('workflow');rows=m.artifact_audit(p);self.assertEqual([r['path'] for r in rows],['execution/.github/workflows/phase27.yml'])
 def test_output_rejects_checkout_before_creation(self):
  with tempfile.TemporaryDirectory() as t:
   repo=Path(t)/'repo';repo.mkdir();out=repo/'build'
   self.assertRaises(ValueError,m.prepare_output,repo,out)
   self.assertFalse(out.exists())
 def test_output_rejects_symlink_into_checkout(self):
  with tempfile.TemporaryDirectory() as t:
   p=Path(t);repo=p/'repo';repo.mkdir();link=p/'alias';link.symlink_to(repo)
   self.assertRaises(ValueError,m.prepare_output,repo,link/'build')
   self.assertFalse((repo/'build').exists())
 def test_output_outside_checkout(self):
  with tempfile.TemporaryDirectory() as t:
   p=Path(t);repo=p/'repo';repo.mkdir();out=p/'build'
   self.assertEqual(m.prepare_output(repo,out),out.resolve())
   self.assertTrue(out.is_dir())
 def test_failure_keeps_real_compiler_diagnostic(self):
  import subprocess
  with tempfile.TemporaryDirectory() as t:
   p=Path(t);phase=p/'phase';stage=phase/'tests/mpv/ci-green';stage.mkdir(parents=True);artifact=p/'artifact';artifact.mkdir()
   src=stage/'broken.c';src.write_text('#error phase27_diagnostic_sentinel\n')
   r=subprocess.run(['clang','-fsyntax-only',str(src)],capture_output=True,text=True)
   self.assertNotEqual(r.returncode,0);(stage/'compile.log').write_text(r.stdout+r.stderr)
   (stage/'harness').write_bytes(b'not-for-upload')
   m.collect_diagnostics(phase,artifact)
   saved=artifact/'results/tests/mpv/ci-green/compile.log'
   self.assertEqual(saved.read_text(),r.stdout+r.stderr)
   self.assertIn('phase27_diagnostic_sentinel',saved.read_text())
   self.assertFalse((saved.parent/'harness').exists())
 def test_failure_diagnostic_symlink_rejected(self):
  with tempfile.TemporaryDirectory() as t:
   p=Path(t);phase=p/'phase';stage=phase/'tests/mpv/ci-green';stage.mkdir(parents=True);artifact=p/'artifact';artifact.mkdir();(p/'secret').write_text('secret');(stage/'compile.log').symlink_to(p/'secret')
   self.assertRaises(ValueError,m.collect_diagnostics,phase,artifact)
if __name__=='__main__':unittest.main()
