import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'device'))
from run import cleanup_pass,completed
class Cases(unittest.TestCase):
 def test_cleanup(self):
  d={'cleanupEvidenceValid':True,'abilityAbsent':True,'windowAbsent':True,'pidAbsent':True};self.assertTrue(cleanup_pass(d))
  for k in d:
   x=d.copy();x[k]=False;self.assertFalse(cleanup_pass(x))
  self.assertFalse(cleanup_pass({}))
 def test_completion(self):
  text='loaded=1 eof=0 errors=0';cmd={'exit':0,'stdout':text};log='P24_BEGIN case=vk-nas-long pid=1\nP24_RESULT '+text
  self.assertTrue(completed('vk-nas-long',cmd,log));self.assertFalse(completed('vk-nas-long',cmd,''));self.assertFalse(completed('vk-nas-long',{'exit':124,'stdout':text},log));self.assertFalse(completed('vk-nas-long',{'exit':0,'stdout':text,'timeout':10},log))
if __name__=='__main__':unittest.main()
