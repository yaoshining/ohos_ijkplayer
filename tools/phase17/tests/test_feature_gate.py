from pathlib import Path
import sys,unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from feature_gate import feature_macros,require_expected_features
class FeatureGateTests(unittest.TestCase):
 def test_define_and_undef_distinct(self):
  self.assertEqual(feature_macros('#undef PL_HAVE_X\n#define PL_HAVE_VULKAN 1\n','PL_HAVE_'),{'PL_HAVE_VULKAN':'1','PL_HAVE_X':None})
 def test_matching_features(self):self.assertTrue(require_expected_features({'libplacebo':{'PL_HAVE_VK_PROC_ADDR':'1'}},{'libplacebo':{'PL_HAVE_VK_PROC_ADDR':'1'}}))
 def test_disabled_probe_feature_rejected(self):
  with self.assertRaises(ValueError):require_expected_features({'libplacebo':{'PL_HAVE_VK_PROC_ADDR':None}},{'libplacebo':{'PL_HAVE_VK_PROC_ADDR':'1'}})
 def test_missing_feature_rejected(self):
  with self.assertRaises(ValueError):require_expected_features({'libplacebo':{}},{'libplacebo':{'PL_HAVE_VK_PROC_ADDR':'1'}})
 def test_missing_duplicate_header_rejected(self):
  for text in ['', '#define HAVE_A 1\n#define HAVE_A 0\n']:
   with self.subTest(text=text),self.assertRaises(ValueError):feature_macros(text,'HAVE_')
