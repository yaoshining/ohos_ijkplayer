from pathlib import Path
import unittest,sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
class Mapping(unittest.TestCase):
 def test_seven_exact_libraries(self):
  from acceptance import accept_libraries
  expected={str(i):str(i)*64 for i in range(7)}
  self.assertTrue(accept_libraries(expected,expected))
  for actual in [{},dict(list(expected.items())[:6]),{**expected,'extra':'0'*64},{**expected,'3':'bad'}]:self.assertFalse(accept_libraries(actual,expected))
