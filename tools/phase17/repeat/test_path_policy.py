from pathlib import Path
import unittest
from path_policy import stable_install_plan,validate_target_config
class PathPolicyTests(unittest.TestCase):
 def test_distinct_staging_roots_share_target_options(self):
  a=stable_install_plan(Path('/a'));b=stable_install_plan(Path('/much/longer/b'))
  self.assertEqual(a['setupArgs'],b['setupArgs']);self.assertEqual(a['setupArgs'],['--cross-file','build-tools/mpv.ini','--prefix=/usr/local'])
  self.assertNotEqual(a['destdir'],b['destdir']);self.assertEqual(a['artifact'],Path('/a/install/usr/local/lib/libmpv.so'))
 def test_stable_generated_target_configuration_accepted(self):
  self.assertTrue(validate_target_config('#define CONFIGURATION "-Dprefix=/usr/local --cross-file=build-tools/mpv.ini"\n#define MPV_CONFDIR "/usr/local/etc/mpv"\n',Path('/a')))
 def test_absolute_crossfile_or_runtime_root_rejected(self):
  for config in ['-Dprefix=/a/install --cross-file=build-tools/mpv.ini','-Dprefix=/usr/local --cross-file=/a/tools.ini','-Dprefix=/usr/local --cross-file=/other/tools.ini']:
   with self.subTest(config=config),self.assertRaises(ValueError):validate_target_config('#define CONFIGURATION "'+config+'"\n#define MPV_CONFDIR "/usr/local/etc/mpv"\n',Path('/a'))
 def test_wrong_or_missing_confdir_rejected(self):
  for config in ['#define CONFIGURATION "--cross-file=build-tools/mpv.ini"\n','#define CONFIGURATION "--cross-file=build-tools/mpv.ini"\n#define MPV_CONFDIR "/a/etc/mpv"\n']:
   with self.subTest(config=config),self.assertRaises(ValueError):validate_target_config(config,Path('/a'))
if __name__=='__main__':unittest.main()
