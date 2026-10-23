from pathlib import Path
import importlib.util,tempfile,unittest
R=Path(__file__).resolve().parents[1]
class FreshBuild(unittest.TestCase):
 def test_existing_output_rejected_before_writes(self):
  s=importlib.util.spec_from_file_location('runtime_build',R/'build.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
  with tempfile.TemporaryDirectory() as t:
   p=Path(t);(p/'marker').write_text('unchanged')
   with self.assertRaises(ValueError):m.require_fresh(p)
   self.assertEqual((p/'marker').read_text(),'unchanged');self.assertEqual(len(list(p.iterdir())),1)
 def test_mismatched_source_rejected(self):
  s=importlib.util.spec_from_file_location('runtime_build',R/'build.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
  with tempfile.TemporaryDirectory() as t:
   p=Path(t)/'input';p.write_bytes(b'wrong')
   with self.assertRaises(ValueError):m.require_sha(p,'0'*64)
 def test_empty_and_incomplete_libraries_rejected_in_each_run(self):
  s=importlib.util.spec_from_file_location('runtime_build',R/'build.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
  for count in [0,5]:
   with self.subTest(count=count),tempfile.TemporaryDirectory() as t:
    p=Path(t)
    for name in list(m.EXPECTED_LIBRARIES)[:count]:(p/name).write_bytes(b'not an ELF')
    for run in range(2):
     with self.assertRaises(ValueError):m.collect_libraries(p,'unavailable-readelf')
