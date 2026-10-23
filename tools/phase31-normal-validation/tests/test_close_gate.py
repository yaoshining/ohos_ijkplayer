import sys,json,unittest,os
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'device'));from close_gate import analyze
F=json.loads((Path(__file__).parent/'fixtures/close.json').read_text());M=F['marker'];B=F['before'];R=F['rows']
if 'PHASE31_RAW_EVIDENCE' in os.environ:
 P=Path(os.environ['PHASE31_RAW_EVIDENCE'])/'device-close-01';M=json.loads((P/'normal-close-request.json').read_text());B=json.loads((P/'before-cleanup.json').read_text());R=[]
 for p in P.glob('timeline-*.jsonl'):R.extend(json.loads(l) for l in p.read_text().splitlines())
class Close(unittest.TestCase):
 def test_real(self):self.assertTrue(analyze(M,B,R)['accepted'])
 def test_false_clean(self):self.assertFalse(analyze(dict(M,cleanBeforeClose=False),B,R)['accepted'])
 def test_offline(self):
  b=dict(B);b['targets']=dict(B['targets'],stdout='Offline');self.assertFalse(analyze(M,b,R)['accepted'])
 def test_missing_destroy(self):self.assertFalse(analyze(M,B,[r for r in R if not(r['event']=='query_end' and r['generation']==103)])['accepted'])
 def test_timeout_absent(self):
  b=dict(B);b['ability']=dict(B['ability'],timeout=15,stdout='');self.assertFalse(analyze(M,b,R)['accepted'])
if __name__=='__main__':unittest.main()
