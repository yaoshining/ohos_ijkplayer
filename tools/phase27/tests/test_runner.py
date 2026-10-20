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
if __name__=='__main__':unittest.main()
