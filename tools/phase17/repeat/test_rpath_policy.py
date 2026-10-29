from pathlib import Path
import unittest
from path_policy import ffmpeg_stage_path,validate_build_rpath,require_no_runtime_paths
class RPathPolicyTests(unittest.TestCase):
 def test_stable_stage_is_declared_child_of_source(self):
  self.assertEqual(ffmpeg_stage_path(True),Path('mpv/source/_staged/ffmpeg'));self.assertEqual(ffmpeg_stage_path(False),Path('ffmpeg'))
 def test_origin_relative_auto_rpath_accepted(self):
  self.assertTrue(validate_build_rpath("clang -Wl,-rpath,'$ORIGIN/../source/_staged/ffmpeg/lib'",Path('/run/a')))
 def test_normalized_relative_directory_is_accepted(self):
  self.assertTrue(validate_build_rpath("clang '-Wl,-rpath,$ORIGIN/../source/_staged/ffmpeg/lib/pkgconfig/../../lib'",Path('/run/b')))
 def test_absolute_missing_or_other_origin_path_rejected(self):
  for cmd in ['clang -Wl,-rpath,/run/a/ffmpeg/lib','clang -Wl,-rpath,/host/lib',"clang '-Wl,-rpath,$ORIGIN/other'",'clang']:
   with self.subTest(cmd=cmd),self.assertRaises(ValueError):validate_build_rpath(cmd,Path('/run/a'))
 def test_installed_runtime_paths_removed(self):
  self.assertTrue(require_no_runtime_paths([]))
  for paths in [['/host/lib'],['$ORIGIN/../source/_staged/ffmpeg/lib'],['']]:
   with self.subTest(paths=paths),self.assertRaises(ValueError):require_no_runtime_paths(paths)
if __name__=='__main__':unittest.main()
