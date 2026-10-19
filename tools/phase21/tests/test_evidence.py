from pathlib import Path
import importlib.util,sys,tempfile,unittest,copy
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R))
import collect
from common import sha
class Evidence(unittest.TestCase):
 def test_runtime_font_selected(self):self.assertTrue(collect.select_file(Path('target/origin-a/runtime-example/resources/fonts/font1.ttf'),'target'))
 def test_native_exact_cases(self):
  rows=[{'case':n,'passed':True} for n in collect.CASES];collect.validate_cases(rows)
  with self.assertRaises(ValueError):collect.validate_cases(rows[:-1])
  with self.assertRaises(ValueError):collect.validate_cases(rows[:-1]+[rows[0]])
 def test_missing_target_library_rejected(self):
  with tempfile.TemporaryDirectory() as td:
   r=Path(td);(r/'a.so').write_bytes(b'a')
   with self.assertRaises((ValueError,FileNotFoundError)):collect.validate_libraries(r,{'a.so':sha(r/'a.so'),'b.so':'0'*64})
 def test_wrong_target_library_rejected(self):
  with tempfile.TemporaryDirectory() as td:
   r=Path(td);(r/'a.so').write_bytes(b'a')
   with self.assertRaises(ValueError):collect.validate_libraries(r,{'a.so':'0'*64})
class TargetInput(unittest.TestCase):
 def test_full_version_resolved(self):
  import build
  with tempfile.TemporaryDirectory() as td:
   r=Path(td);p=r/'libtest.so.1.2.3';p.write_bytes(b'fixed');self.assertEqual(build.resolve_library(r,'libtest.so.1',sha(p)),p.resolve())
 def test_multiple_candidates_rejected(self):
  import build
  with tempfile.TemporaryDirectory() as td:
   r=Path(td);a=r/'libtest.so.1.2';a.write_bytes(b'a');(r/'libtest.so.1.3').write_bytes(b'a')
   with self.assertRaises(ValueError):build.resolve_library(r,'libtest.so.1',sha(a))
 def test_missing_candidate_rejected(self):
  import build
  with tempfile.TemporaryDirectory() as td:
   with self.assertRaises(ValueError):build.resolve_library(Path(td),'libtest.so.1','0'*64)
class FixtureCollection(unittest.TestCase):
 def test_permission_negative_restored_for_collection(self):
  import native,shutil
  with tempfile.TemporaryDirectory() as td:
   r=Path(td);p=r/'resources/fonts/font1.ttf';p.parent.mkdir(parents=True);p.write_bytes(b'original');p.chmod(0)
   rows=native.restore_fixture_permissions(r);self.assertEqual(rows[0]['before'],0);shutil.copyfile(p,r/'downloaded.ttf');self.assertEqual((r/'downloaded.ttf').read_bytes(),b'original')

class HostProfile(unittest.TestCase):
 def test_software_profile_explicitly_disables_default_enabled_gl(self):
  import native
  opts=native.host_mpv_options()
  for option in ['-Dgl=disabled','-Dohos=disabled','-Degl-ohos=disabled','-Dauto_features=disabled']:self.assertIn(option,opts)
