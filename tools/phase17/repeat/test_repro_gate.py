import copy,tempfile,unittest
from pathlib import Path
from repro_gate import require_fresh,compare_runs
class FreshTests(unittest.TestCase):
 def test_missing_root_allowed(self):
  with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as d:self.assertEqual(require_fresh(Path(d)/'new'),(Path(d)/'new').resolve())
 def test_existing_empty_or_populated_root_rejected(self):
  with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as d:
   with self.assertRaises(ValueError):require_fresh(Path(d))
   (Path(d)/'old.o').write_bytes(b'old')
   with self.assertRaises(ValueError):require_fresh(Path(d))
 def test_dangling_symlink_rejected(self):
  with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as d:
   p=Path(d)/'root';p.symlink_to(Path(d)/'absent')
   with self.assertRaises(ValueError):require_fresh(p)
class ReproTests(unittest.TestCase):
 def setUp(self):
  self.a={'runRoot':'/clean-a','freshRootVerified':True,'configuration':{'options':['release'],'toolSha256':'tool','packageSHA256':'inputs'},'linkInputs':[{'path':'deps/lib/a.a','sha256':'a'}],'artifactHashes':{'mpv':'m','libplacebo':'p'},'allocatedSections':{'.text':{'sha256':'text','size':4}},'exports':['mpv_create'],'imports':['av_x@LIBAVCODEC_62'],'features':{'ohcodec':True},'archiveMembers':[{'name':'a.o','sha256':'o'}]};self.b=copy.deepcopy(self.a);self.b['runRoot']='/longer/clean-b'
 def test_equal_across_different_roots(self):self.assertTrue(compare_runs(self.a,self.b)['passed'])
 def test_deliberate_output_difference_rejected(self):
  self.b['artifactHashes']['mpv']='different';r=compare_runs(self.a,self.b);self.assertFalse(r['passed']);self.assertIn('artifactHashes',r['differentFields'])
 def test_configuration_or_link_input_mismatch_rejected(self):
  for key in ['configuration','linkInputs']:
   b=copy.deepcopy(self.b);b[key]={}
   with self.subTest(key=key):self.assertIn(key,compare_runs(self.a,b)['differentFields'])
 def test_section_exports_imports_features_or_member_difference_rejected(self):
  for key in ['allocatedSections','exports','imports','features','archiveMembers']:
   b=copy.deepcopy(self.b);b[key]={}
   with self.subTest(key=key):self.assertIn(key,compare_runs(self.a,b)['differentFields'])
 def test_same_root_or_missing_fresh_evidence_rejected(self):
  for value in [False,None]:
   b=copy.deepcopy(self.b);b['freshRootVerified']=value
   with self.subTest(value=value),self.assertRaises(ValueError):compare_runs(self.a,b)
  self.b['runRoot']=self.a['runRoot']
  with self.assertRaises(ValueError):compare_runs(self.a,self.b)
 def test_missing_required_evidence_fails_closed(self):
  del self.b['linkInputs']
  with self.assertRaises(ValueError):compare_runs(self.a,self.b)
if __name__=='__main__':unittest.main()
