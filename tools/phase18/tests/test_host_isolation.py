from pathlib import Path
import unittest
R=Path(__file__).resolve().parents[3]
class HostIsolation(unittest.TestCase):
 def test_no_system_pip_install(self):
  workflow=(R/'.github/workflows/phase18-dependency-closure.yml').read_text()
  self.assertNotIn('python3 -m pip install',workflow)
 def test_setup_uses_virtual_environment(self):
  script=(R/'tools/phase18/host_setup.py').read_text()
  self.assertIn("'-m','venv'",script)
  self.assertIn("venv/'bin/python'",script)
  self.assertIn('--require-hashes',script)
