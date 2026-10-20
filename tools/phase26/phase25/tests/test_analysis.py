import importlib.util,json,tempfile,unittest
from pathlib import Path
spec=importlib.util.spec_from_file_location('analysis',Path(__file__).parents[1]/'tools/analyze_timeline.py')
a=importlib.util.module_from_spec(spec);spec.loader.exec_module(a)
def rows():
 events=['session_begin','ability_foreground','window_inactive','run_begin','sample_begin','query_begin','heartbeat','overdue','query_end','sample_end','window_active','heartbeat','run_end','session_end']
 return [dict(schema=1,session='a-1-b',seq=i+1,lane=2 if e in ('heartbeat','overdue') else 1 if e.startswith(('query_','sample_','run_')) else 0,event=e,key={4:4,7:6,8:6,9:5,12:4}.get(i,0),generation=1,monoNs=(i+1)*1000000000,wallNs=(i+1)*1000000000,durationNs=3000000000 if i==8 else 0,rc=0) for i,e in enumerate(events)]
class AnalysisTest(unittest.TestCase):
 def test_normal_and_focus(self):
  r=a.analyze(rows());self.assertTrue(r['complete']);self.assertFalse(r['backgroundObserved']);self.assertEqual(r['pairedQueries'],1)
 def test_missing_duplicate_unfinished(self):
  for v in [rows()[:-1],rows()[1:],rows()+[rows()[2]],rows()[:7]+rows()[8:]]:self.assertFalse(a.analyze(v)['complete'])
 def test_background_not_cleared_by_focus(self):
  x=rows();x[2]['event']='ability_background';r=a.analyze(x);self.assertTrue(r['backgroundObserved']);self.assertFalse(r['continuousEligible'])
 def test_bad_logging(self):
  x=rows();x[-1]['rc']=1;self.assertFalse(a.analyze(x)['complete'])
 def test_late_and_subscription(self):
  for e in ['subscription_failed','logging_error']:
   x=rows();x[2]['event']=e;self.assertFalse(a.analyze(x)['complete'])
 def test_wall_adjustment(self):
  x=rows();x[8]['wallNs']=-1;self.assertTrue(a.analyze(x)['wallClockAdjustment']);self.assertTrue(a.analyze(x)['complete'])
 def test_heartbeat_gap(self):
  x=rows()
  for r in x[6:]:r['monoNs']+=300000000000;r['wallNs']+=300000000000
  r=a.analyze(x);self.assertFalse(r['continuousEligible']);self.assertFalse(r['coverageComplete'])
 def test_property_mismatch(self):
  x=rows();x[8]['generation']=999;self.assertFalse(a.analyze(x)['complete'])
 def test_actual_call_interval(self):
  x=rows();x[8]['callStartNs']=x[8]['monoNs']+1
  self.assertFalse(a.analyze(x)['complete'])
 def test_schema_and_identity(self):
  for key,value in [('schema',2),('lane',9),('event','unknown'),('seq',True),('session',None)]:
   x=rows();x[0][key]=value;self.assertFalse(a.analyze(x)['complete'])
 def test_duplicate_session_boundaries(self):
  x=rows();x[2]['event']='session_begin';self.assertFalse(a.analyze(x)['complete'])
 def test_empty_run_not_eligible(self):
  x=[r for r in rows() if r['event'] in ('session_begin','heartbeat','session_end')]
  for i,r in enumerate(x):r['seq']=i+1
  self.assertFalse(a.analyze(x)['continuousEligible'])
 def test_truncation(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/'x.jsonl';p.write_text(json.dumps(rows()[0])+'\n{"seq":2')
   data,errors=a.read_lanes([p]);self.assertTrue(errors);self.assertFalse(a.analyze(data,errors)['complete'])
if __name__=='__main__':unittest.main()
