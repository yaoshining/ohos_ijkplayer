import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from evidence_contract import exact_set, compare_archive_rows, verify_index
class Contracts(unittest.TestCase):
 def test_set_order(self):self.assertTrue(exact_set(['a','b'],['b','a']))
 def test_set_same_count_wrong(self):
  with self.assertRaises(ValueError):exact_set(['a','b@2'],['a','b@1'])
 def test_set_duplicate(self):
  with self.assertRaises(ValueError):exact_set(['a','a'],['a'])
 def test_set_missing(self):
  with self.assertRaises(ValueError):exact_set(['a'],['a','b'])
 def test_archives_normal(self):self.assertTrue(compare_archive_rows([{'path':'a','sha256':'s'}],[{'path':'a','sha256':'s'}],['a']))
 def test_archives_forged_package(self):
  with self.assertRaises(ValueError):compare_archive_rows([{'path':'a','sha256':'old'}],[{'path':'a','sha256':'new'}],['a'])
 def test_archives_duplicate(self):
  with self.assertRaises(ValueError):compare_archive_rows([{'path':'a','sha256':'s'}]*2,[{'path':'a','sha256':'s'}],['a'])
 def test_archives_extra(self):
  with self.assertRaises(ValueError):compare_archive_rows([{'path':'a','sha256':'s'},{'path':'b','sha256':'s'}],[{'path':'a','sha256':'s'}],['a'])
 def test_index_exact(self):self.assertTrue(verify_index([{'path':'a','size':3,'sha256':'s'}],{'a':(3,'s')}))
 def test_index_extra(self):
  with self.assertRaises(ValueError):verify_index([{'path':'a','size':3,'sha256':'s'}],{'a':(3,'s'),'b':(0,'x')})
 def test_index_corrupt(self):
  with self.assertRaises(ValueError):verify_index([{'path':'a','size':3,'sha256':'s'}],{'a':(3,'x')})
 def test_index_escape(self):
  with self.assertRaises(ValueError):verify_index([{'path':'../a','size':3,'sha256':'s'}],{'../a':(3,'s')})
 def test_index_duplicate(self):
  with self.assertRaises(ValueError):verify_index([{'path':'a','size':3,'sha256':'s'}]*2,{'a':(3,'s')})

class BeforePins(unittest.TestCase):
 def test_missing_before_pin(self):
  from evidence_contract import require_before_pin
  with self.assertRaises(ValueError):require_before_pin('/sdk/header','s',{})
 def test_changed_before_pin(self):
  from evidence_contract import require_before_pin
  with self.assertRaises(ValueError):require_before_pin('/sdk/header','new',{'/sdk/header':'old'})
 def test_same_before_pin(self):
  from evidence_contract import require_before_pin
  self.assertTrue(require_before_pin('/sdk/header','s',{'/sdk/header':'s'}))

class HostEvidenceSelection(unittest.TestCase):
 def test_packages(self):
  from evidence_contract import host_package_file
  self.assertTrue(host_package_file('debs/gperf_3.1_amd64.deb'));self.assertTrue(host_package_file('wheels/meson.whl'))
 def test_locks_and_partial_rejected(self):
  from evidence_contract import host_package_file
  for p in ['debs/lock','debs/partial/unfinished.deb','wheels/unknown','venv/lib/a.deb']:
   self.assertFalse(host_package_file(p),p)
