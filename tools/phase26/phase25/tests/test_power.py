import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parents[1]/'tools'))
from power_state import parse_power
class PowerTest(unittest.TestCase):
 def test_current_not_history(self):self.assertEqual(parse_power('Current State: SLEEP  Reason: 4\nState: AWAKE Reason: SHELL'),'SLEEP')
 def test_awake(self):self.assertEqual(parse_power('Current State: AWAKE Reason: 1\nState: SLEEP'),'AWAKE')
 def test_missing(self):self.assertEqual(parse_power('State: AWAKE'),'unknown')
if __name__=='__main__':unittest.main()
