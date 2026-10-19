from pathlib import Path
import importlib.util,os,subprocess,tempfile,unittest,shutil
R=Path(__file__).resolve().parents[1]
class Factory(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.tmp=tempfile.TemporaryDirectory();cls.exe=Path(cls.tmp.name)/'factory'
  inc=Path(cls.tmp.name)/'include/libavformat';inc.mkdir(parents=True)
  shutil.copyfile(R.parent/'phase20/runtime/smb_runtime.h',inc/'ohcodec_smb_runtime.h')
  subprocess.run(['cc','-std=c11','-Wall','-Wextra','-Werror','-I'+str(R),'-I'+str(R/'tests/stubs'),'-I'+str(inc.parent),str(R/'tests/factory.c'),str(R/'integration.c'),'-o',str(cls.exe)],check=True)
 @classmethod
 def tearDownClass(cls):cls.tmp.cleanup()
 def test_success_order_and_idempotent_destroy(self):self.run_case(0)
 def test_resource_failure_before_samba(self):self.run_case(1)
 def test_samba_failure_before_allocation(self):self.run_case(2)
 def test_allocation_failure(self):self.run_case(3)
 def test_option_failure_cleans_handle(self):self.run_case(4)
 def test_initialize_failure_cleans_handle(self):self.run_case(5)
 def test_late_option_failure(self):self.run_case(6)
 def test_null_config(self):self.run_case(7)
 def test_null_output(self):self.run_case(8)
 def test_optional_error(self):self.run_case(9)
 def run_case(self,n):
  r=subprocess.run([str(self.exe),str(n)],capture_output=True,text=True);self.assertEqual(r.returncode,0,r.stdout+r.stderr)
class Resources(unittest.TestCase):
 def module(self):
  s=importlib.util.spec_from_file_location('p21_resources',R/'resources.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
 def test_fresh_layout_and_fixed_font(self):
  m=self.module()
  with tempfile.TemporaryDirectory() as t:
   root=Path(t)/'new';d=m.prepare(root)
   for rel in ['state/private','state/state','state/lock','cache/demux','resources/fonts'] :self.assertTrue((root/rel).is_dir())
   self.assertEqual(m.digest(root/'resources/fonts/font1.ttf'),m.FONT_SHA)
   self.assertEqual(set(d),{'config_file','state_root','cache_root','resource_root'})
   self.assertEqual(list(root.rglob('*.pyc')),[])
 def test_reject_existing_root(self):
  m=self.module()
  with tempfile.TemporaryDirectory() as t:
   with self.assertRaises(FileExistsError):m.prepare(Path(t))
 def test_reject_corrupt_font_before_creation(self):
  m=self.module()
  with tempfile.TemporaryDirectory() as t:
   p=Path(t)/'font';p.write_bytes(b'bad');root=Path(t)/'new'
   with self.assertRaises(ValueError):m.prepare(root,p)
   self.assertFalse(root.exists())
