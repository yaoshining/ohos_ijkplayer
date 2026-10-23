import importlib.util
from pathlib import Path
import unittest
p=Path(__file__).resolve().parents[1]/"resource_summary.py"
s=importlib.util.spec_from_file_location("summary",p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
class ResourceSummary(unittest.TestCase):
 def cases(self):
  return [{'mode':'vk-h264','cycle':i,'surface':'1','pid':1,'mappedSevenMatch':True,
   'result':'loaded=1 eof=1 observedDistinctPlaybackPTSWithFrame=10 gpu=ohosvk hwdec=ohcodec seekConfirmed=1 stopped=0',
   'samples':{'settled3000':{'reportedFd':i+2,'fds':[{'target':'anon_inode:dmabuf','fd':j}for j in range(i)]}}}
   for i in range(1,14)]
 def test_two_temporary_fds_in_original_usage_scope(self):
  self.assertEqual(m.summarize(self.cases(),'vk-h264')['status'],'persistent-growth')
 def test_missing_fd_details_remain_incomplete(self):
  rows=self.cases();rows[-1]['samples']['settled3000']['fds'].pop()
  self.assertEqual(m.summarize(rows,'vk-h264')['status'],'incomplete')
 def test_mixed_processes_cannot_form_a_matrix(self):
  rows=self.cases()
  for i,c in enumerate(rows):c['pid']=1 if i<7 else 2
  self.assertEqual(m.summarize(rows,'vk-h264')['status'],'incomplete')
 def test_stepwise_growth_is_not_stability(self):
  rows=self.cases()
  for i,c in enumerate(rows):
   n=i//2;c['samples']['settled3000']={'reportedFd':n+2,'fds':[{'target':'dmabuf'}for _ in range(n)]}
  self.assertEqual(m.summarize(rows,'vk-h264')['status'],'net-growth')
 def test_frames_without_eof_seek_or_hardware_are_not_complete(self):
  for marker in ['eof=1','seekConfirmed=1','hwdec=ohcodec','loaded=1','stopped=0']:
   with self.subTest(marker=marker):
    rows=self.cases();rows[-1]['result']=rows[-1]['result'].replace(marker,'')
    self.assertEqual(m.summarize(rows,'vk-h264')['status'],'incomplete')
 def test_unknown_process_is_not_a_verified_single_process(self):
  rows=self.cases()
  for row in rows: row['pid']=None
  self.assertEqual(m.summarize(rows,'vk-h264')['status'],'incomplete')
if __name__=="__main__":unittest.main()
