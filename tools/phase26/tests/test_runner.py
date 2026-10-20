import importlib.util,json,tempfile,unittest,hashlib,sys
from pathlib import Path
P=Path(__file__).parents[1]
s=importlib.util.spec_from_file_location("runner",P/"runner.py");r=importlib.util.module_from_spec(s);s.loader.exec_module(r)
class Runner(unittest.TestCase):
 def fixture(self,root):
  (root/"phase25").mkdir();(root/"phase25/a.py").write_text("print(1)\n")
  data=(root/"phase25/a.py").read_bytes();m={"files":[{"path":"phase25/a.py","size":len(data),"sha256":hashlib.sha256(data).hexdigest()}]};(root/"sources.json").write_text(json.dumps(m));return m
 def test_source_valid_and_drift(self):
  with tempfile.TemporaryDirectory() as t:
   root=Path(t);self.fixture(root);self.assertEqual(len(r.verify_sources(root)),1);(root/"phase25/a.py").write_text("print(2)\n")
   with self.assertRaises(ValueError):r.verify_sources(root)
 def test_source_missing_and_symlink(self):
  with tempfile.TemporaryDirectory() as t:
   root=Path(t);self.fixture(root);a=root/"phase25/a.py";a.unlink()
   with self.assertRaises(ValueError):r.verify_sources(root)
   (root/"real").write_text("print(1)\n");a.symlink_to(root/"real")
   with self.assertRaises(ValueError):r.verify_sources(root)
 def test_escape_and_sensitive_manifest_rejected(self):
  with tempfile.TemporaryDirectory() as t:
   root=Path(t);m=self.fixture(root)
   for name in ["../outside","private/a.py","phase25/credentials.json","phase25/a.hap"]:
    m["files"][0]["path"]=name;(root/"sources.json").write_text(json.dumps(m))
    with self.assertRaises(ValueError):r.verify_sources(root)
 def test_failure_status_and_original_rc(self):
  with tempfile.TemporaryDirectory() as t:
   out=Path(t);record={"commands":[]};rc=r.run_step("failure",[sys.executable,"-B","-c","import sys;print('real failure');sys.exit(7)"],out,record)
   self.assertEqual(rc,7);self.assertEqual(record["commands"][0]["returncode"],7);self.assertIn("real failure",(out/"failure.log").read_text())
 def test_collector_does_not_sweep_sentinels(self):
  with tempfile.TemporaryDirectory() as t:
   root=Path(t)/"src";root.mkdir();self.fixture(root);out=Path(t)/"out";out.mkdir();(out/"record.json").write_text('{"status":"failed","commands":[]}')
   for name in ["credentials.json","nas.bin","secret.hap"]:(out/name).write_text("sentinel")
   (out/"private").mkdir();(out/"private/secret").write_text("sentinel")
   dest=Path(t)/"artifact";r.collect(root,out,dest);names=[str(p.relative_to(dest)) for p in dest.rglob("*") if p.is_file()];self.assertNotIn("credentials.json",names);self.assertEqual(json.loads((dest/"record.json").read_text())["status"],"failed")
 def test_collector_missing_record_fails(self):
  with tempfile.TemporaryDirectory() as t:
   root=Path(t);self.fixture(root)
   with self.assertRaises(ValueError):r.collect(root,root,root/"artifact")
 def test_execution_inputs_bound(self):
  rows=r.execution_sources(P)
  self.assertTrue(any(x['path'].endswith('runner.py') for x in rows))
  self.assertTrue(any(x['path'].endswith('test_getter.cpp') for x in rows))
  self.assertTrue(any(x['path'].endswith('phase26-validation.yml') for x in rows))
  self.assertTrue(all(len(x['sha256'])==64 for x in rows))
 def test_collection_failure_cannot_report_pass(self):
  from unittest.mock import patch
  with tempfile.TemporaryDirectory() as t:
   out=Path(t);record={'commands':[],'testsPassed':True,'status':'passed'}
   with patch.object(r,'collect',side_effect=ValueError('test collection failure')):rc=r.finalize(P,out,record,0)
   self.assertNotEqual(rc,0);data=json.loads((out/'record.json').read_text());self.assertTrue(data['testsPassed']);self.assertFalse(data['collectionComplete']);self.assertEqual(data['status'],'failed')
if __name__=="__main__":unittest.main()
