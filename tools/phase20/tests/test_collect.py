from pathlib import Path
import importlib.util,tempfile,unittest
R=Path(__file__).resolve().parents[1]
class Collection(unittest.TestCase):
 def module(self):
  import sys
  sys.path.insert(0,str(R));s=importlib.util.spec_from_file_location('collect_runtime',R/'collect.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
 def test_missing_success_outputs_rejected(self):
  m=self.module()
  with tempfile.TemporaryDirectory() as t:
   for kind in ['native','target']:
    with self.subTest(kind=kind),self.assertRaises((ValueError,FileNotFoundError)):m.validate_success(Path(t),kind)
 def test_input_sdk_always_excluded(self):
  m=self.module()
  for path in ['inputs/sdk/sysroot/lib/libc.a','inputs/config.h','inputs/target-sdk.json']:
   self.assertFalse(m.select_file(Path(path)))
