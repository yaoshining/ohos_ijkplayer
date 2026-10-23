"""CI 接受/上传边界回归；不访问设备或网络。"""
import importlib.util
import json
from pathlib import Path
import tempfile
import subprocess
import unittest
spec=importlib.util.spec_from_file_location('runner',Path(__file__).with_name('runner.py'))
runner=importlib.util.module_from_spec(spec);spec.loader.exec_module(runner)
class GateTests(unittest.TestCase):
 def test_results_require_count_and_every_case(self):
  self.assertTrue(runner.accepted_result({'accepted':True,'cases':[{'passed':True}]*12},12))
  for d in ({'accepted':True,'cases':[]},{'accepted':False,'cases':[{'passed':True}]*12},{'accepted':True,'cases':[{'passed':True}]*11+[{'passed':False}]}):
   self.assertFalse(runner.accepted_result(d,12))
 def test_mutant_requires_actual_close_failure(self):
  d={'compileExit':0,'accepted':False,'cases':[{'case':'callback-inflight-close','exitCode':1,'expected':False,'stdout':'FAIL callback-inflight-close: Close did not wait for callback completion'}]}
  self.assertTrue(runner.mutant_rejected(1,d))
  self.assertFalse(runner.mutant_rejected(0,d))
  d['compileExit']=1
  self.assertFalse(runner.mutant_rejected(1,d))
  self.assertFalse(runner.mutant_rejected(1,{}))
 def test_export_only_regular_utf8_allowlist(self):
  with tempfile.TemporaryDirectory() as t:
   root=Path(t);src=root/'src';src.mkdir();out=root/'out'
   (src/'test.log').write_text('failed evidence\n');(src/'result.json').write_text('{}')
   (src/'harness').write_bytes(b'\x7fELF');(src/'private.hap').write_bytes(b'PK')
   (src/'link.log').symlink_to(src/'test.log')
   runner.export_evidence(src,out)
   self.assertEqual(sorted(p.name for p in out.iterdir()),['result.json','test.log'])
 def test_manifest_rejects_changed_and_extra_inputs(self):
  with tempfile.TemporaryDirectory() as t:
   p=Path(t);(p/'x.c').write_text('x')
   index={'files':[{'path':'x.c','sha256':runner.sha(p/'x.c'),'size':1}]}
   (p/'source-index.json').write_text(json.dumps(index));runner.verify_inputs(p)
   (p/'x.c').write_text('y')
   with self.assertRaises(ValueError):runner.verify_inputs(p)
   (p/'x.c').write_text('x');(p/'unknown').write_text('x')
   with self.assertRaises(ValueError):runner.verify_inputs(p)
 def test_identity_rejects_dirty_and_inside_output(self):
  with tempfile.TemporaryDirectory() as t:
   r=Path(t)/'repo';r.mkdir()
   subprocess.run(['git','init',str(r)],check=True,capture_output=True)
   subprocess.run(['git','-C',str(r),'config','user.email','test@example.invalid'],check=True)
   subprocess.run(['git','-C',str(r),'config','user.name','Test'],check=True)
   (r/'tracked').write_text('x')
   subprocess.run(['git','-C',str(r),'add','tracked'],check=True)
   subprocess.run(['git','-C',str(r),'commit','-m','test'],check=True,capture_output=True)
   self.assertTrue(runner.identity(r,Path(t)/'out',False)['clean'])
   with self.assertRaises(ValueError):runner.identity(r,r/'out',False)
   (r/'tracked').write_text('y')
   with self.assertRaises(ValueError):runner.identity(r,Path(t)/'out',False)
   self.assertFalse(runner.identity(r,Path(t)/'out',True)['exactCommitReplay'])
 def test_nontext_required_log_fails(self):
  with tempfile.TemporaryDirectory() as t:
   p=Path(t);src=p/'src';src.mkdir();(src/'result.json').write_bytes(b'\x00')
   with self.assertRaises(ValueError):runner.export_evidence(src,p/'out')
 def test_timeout_output_normalization(self):
  self.assertEqual(runner.output_text(b'abc'),'abc')
  self.assertEqual(runner.output_text('abc'),'abc')
  self.assertEqual(runner.output_text(None),'')
 def test_collection_failure_never_exports_success(self):
  with tempfile.TemporaryDirectory() as t:
   p=Path(t);work=p/'work';work.mkdir();artifact=p/'artifact'
   (work/'zz-bad.log').write_bytes(b'\x00bad')
   result={'accepted':True}
   runner.finalize(work,artifact,result,[])
   actual=json.loads((artifact/'result.json').read_text())
   self.assertFalse(actual['accepted']);self.assertFalse(actual['collectionPassed'])
   self.assertFalse((artifact/'artifact-index.json').exists())
 def test_collection_success_has_matching_final_index(self):
  with tempfile.TemporaryDirectory() as t:
   p=Path(t);work=p/'work';work.mkdir();artifact=p/'artifact'
   result={'accepted':True};runner.finalize(work,artifact,result,[])
   actual=json.loads((artifact/'result.json').read_text())
   self.assertTrue(actual['accepted']);self.assertTrue(actual['collectionPassed'])
   idx=json.loads((artifact/'artifact-index.json').read_text())
   for row in idx['files']:self.assertEqual(row['sha256'],runner.sha(artifact/row['path']))
if __name__=='__main__':unittest.main()
