"""真实 static_input：清单之外的 include/pkg-config 输入必须拒绝。"""
import hashlib,importlib.util,json,tempfile,types,unittest
from pathlib import Path
s=importlib.util.spec_from_file_location('sdk_set',Path(__file__).parents[1]/'producer-sdk.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
class Tests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name)
  def row(name):
   p=self.root/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(name.encode());return m.record(p,self.root)
  self.data={'targetAbi':'arm64-v8a','sourceBuildComplete':True,'fullyVerified':False,'archives':[row(n) for n in m.LOCK['staticInputs']],'headers':[row('include/nested/a.h')],'pkgconfig':[row('lib/pkgconfig/a.pc')]}
 def run_input(self):
  p=self.root/'manifest.json';p.write_text(json.dumps(self.data));return m.static_input(types.SimpleNamespace(smb=self.root,static_manifest=p,static_manifest_sha256=m.sha(p)))
 def test_exact_set(self):self.assertEqual(set(self.run_input()),set(m.LOCK['staticInputs']))
 def test_added_input(self):
  for path in ['include/extra.h','include/nested/no-extension','lib/pkgconfig/extra.pc','lib/pkgconfig/extra.conf']:
   p=self.root/path;p.write_text('extra')
   with self.assertRaises(ValueError,msg=path):self.run_input()
   p.unlink()
 def test_duplicate_rows(self):
  for group in ['headers','pkgconfig']:
   self.data[group].append(dict(self.data[group][0]))
   with self.assertRaises(ValueError,msg=group):self.run_input()
   self.data[group].pop()
 def test_missing_row(self):
  self.data['headers']=[]
  with self.assertRaises(ValueError):self.run_input()
 def test_missing_file(self):
  (self.root/'include/nested/a.h').unlink()
  with self.assertRaises(ValueError):self.run_input()
 def test_cross_group(self):
  self.data['headers'],self.data['pkgconfig']=self.data['pkgconfig'],self.data['headers']
  with self.assertRaises(ValueError):self.run_input()
 def test_noncanonical_path(self):
  for value in ['include/./nested/a.h','include//nested/a.h','../a.h','/tmp/a.h']:
   self.data['headers'][0]['path']=value
   with self.assertRaises(ValueError,msg=value):self.run_input()
 def test_symlink_inputs(self):
  p=self.root/'include/alias.h';p.symlink_to('nested/a.h');self.data['headers'].append(m.record(p,self.root))
  with self.assertRaises(ValueError):self.run_input()
 def test_symlink_directory(self):
  p=self.root/'include';p.rename(self.root/'real-include');p.symlink_to('real-include',target_is_directory=True)
  with self.assertRaises(ValueError):self.run_input()
 def test_unrelated_file_ignored(self):
  (self.root/'readme.txt').write_text('not a compiler input');self.run_input()
if __name__=='__main__':unittest.main()
