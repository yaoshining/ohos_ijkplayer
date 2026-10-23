import importlib.util,os,sys,tempfile,unittest
from pathlib import Path
R=Path(__file__).resolve().parents[1]
FILES=['source/shaderc/utils/update_build_version.py','source/shaderc/third_party/spirv-tools/utils/update_build_version.py']
class VersionBoundary(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name)
 def modules(self):
  for i,f in enumerate(FILES):
   s=importlib.util.spec_from_file_location('version'+str(i),R/'source-package'/f);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);yield m
 def test_marker_overrides_parent_git(self):
  (self.root/'.phase18-source-version').write_text('a'*40+'\n')
  for m in self.modules():self.assertEqual(m.describe(str(self.root)),'a'*40)
 def test_no_fallback_missing(self):
  for m in self.modules():
   with self.assertRaises(RuntimeError):m.describe(str(self.root))
 def test_bad_marker_rejected(self):
  (self.root/'.phase18-source-version').write_text('not-a-commit\n')
  for m in self.modules():
   with self.assertRaises(RuntimeError):m.describe(str(self.root))
 def test_ambient_override_disabled(self):
  s=(R/'source-package'/FILES[1]).read_text();self.assertNotIn('os.getenv("FORCED_BUILD_VERSION_DESCRIPTION"',s)
if __name__=='__main__':unittest.main()
