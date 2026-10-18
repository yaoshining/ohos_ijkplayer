import unittest,copy,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from ci_contract import validate_claim
class CIContract(unittest.TestCase):
 def setUp(self):
  self.good={'runUrl':'https://github.com/yaoshining/ohos_ijkplayer/actions/runs/123','commit':'a'*40,'platform':'Linux','runner':'ubuntu-22.04','coverage':'actual-cross-build','comparisonPassed':True,'runs':[{'root':'/tmp/a','fresh':True,'artifactSha256':'b'*64,'steps':{n:0 for n in ['libplacebo-build','libplacebo-install','mpv-build','mpv-install','mpv-strip','static-validation'] }},{'root':'/tmp/longer/b','fresh':True,'artifactSha256':'b'*64,'steps':{n:0 for n in ['libplacebo-build','libplacebo-install','mpv-build','mpv-install','mpv-strip','static-validation']}}]}
 def test_real_cross_build(self):self.assertTrue(validate_claim(self.good))
 def test_gates_only(self):
  self.good['coverage']='tests-only'
  with self.assertRaises(ValueError):validate_claim(self.good)
 def test_failed_compile(self):
  self.good['runs'][0]['steps']['mpv-build']=1
  with self.assertRaises(ValueError):validate_claim(self.good)
 def test_same_directory(self):
  self.good['runs'][1]['root']='/tmp/a'
  with self.assertRaises(ValueError):validate_claim(self.good)
 def test_absent_fresh(self):
  self.good['runs'][0]['fresh']=False
  with self.assertRaises(ValueError):validate_claim(self.good)
 def test_bad_commit(self):
  self.good['commit']='HEAD'
  with self.assertRaises(ValueError):validate_claim(self.good)
 def test_false_repro(self):
  self.good['runs'][1]['artifactSha256']='c'*64
  with self.assertRaises(ValueError):validate_claim(self.good)
if __name__=='__main__':unittest.main()
