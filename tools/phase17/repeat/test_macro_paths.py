from pathlib import Path
import unittest
from path_policy import macro_prefix_arg,require_no_root_bytes
class MacroPathTests(unittest.TestCase):
 def test_maps_only_explicit_run_root_to_stable_dot(self):
  self.assertEqual(macro_prefix_arg(Path('/clean/a')),'-fmacro-prefix-map=/clean/a=.');self.assertEqual(macro_prefix_arg(Path('/longer/b')),'-fmacro-prefix-map=/longer/b=.')
 def test_ambiguous_mapping_path_rejected(self):
  with self.assertRaises(ValueError):macro_prefix_arg(Path('/bad=path'))
 def test_allocated_without_build_root_accepted(self):
  self.assertTrue(require_no_root_bytes([b'code',b'./libplacebo/install/include/header.h\0'],Path('/run/a')))
 def test_header_macro_build_root_in_any_allocated_part_rejected(self):
  with self.assertRaises(ValueError):require_no_root_bytes([b'code',b'/run/a/libplacebo/install/include/libplacebo/utils/libav_internal.h\0'],Path('/run/a'))
 def test_missing_allocated_evidence_rejected(self):
  with self.assertRaises(ValueError):require_no_root_bytes([],Path('/run/a'))
if __name__=='__main__':unittest.main()
