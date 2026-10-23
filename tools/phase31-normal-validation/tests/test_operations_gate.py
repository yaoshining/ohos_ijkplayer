import sys,unittest,re,json,os
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'device'));from operations_gate import analyze
TEXT=(Path(os.environ['PHASE31_RAW_EVIDENCE'])/'device-nas-ops-01/vk-nas-ops-0.log' if 'PHASE31_RAW_EVIDENCE' in os.environ else Path(__file__).parent/'fixtures/operations.log').read_text()
class Operations(unittest.TestCase):
 def test_single_nan_timestamp(self):
  lines=TEXT.splitlines()
  for i,l in enumerate(lines):
   if l.startswith('P31_SAMPLE '):
    d=json.loads(l[11:]);d['t']=float('nan');lines[i]='P31_SAMPLE '+json.dumps(d);break
  self.assertFalse(analyze('\n'.join(lines))['accepted'])
 def test_real_positive(self):self.assertTrue(analyze(TEXT)['accepted'])
 def test_missing_seek(self):self.assertFalse(analyze(re.sub(r'P24_SEEK[^\n]*','',TEXT))['accepted'])
 def test_stale_restart(self):self.assertFalse(analyze(re.sub(r'P24_PLAYBACK_RESTART t=[\d.]+','P24_PLAYBACK_RESTART t=0',TEXT))['accepted'])
 def test_wrong_target(self):
  rows=[]
  for l in TEXT.splitlines():
   if l.startswith('P31_SAMPLE '):
    d=json.loads(l[11:]);d['pts']=100 if d['pts'] is not None else None;l='P31_SAMPLE '+json.dumps(d)
   rows.append(l)
  self.assertFalse(analyze('\n'.join(rows))['accepted'])
 def test_pause_interrupted(self):
  lines=TEXT.splitlines();done=False
  for i,l in enumerate(lines):
   if l.startswith('P31_SAMPLE '):
    d=json.loads(l[11:])
    if d['stage']==3 and d['pause']==1 and not done:d['pause']=0;lines[i]='P31_SAMPLE '+json.dumps(d);done=True
  self.assertFalse(analyze('\n'.join(lines))['accepted'])
 def test_action_failure(self):self.assertFalse(analyze(TEXT.replace('kind=1 begin=4.819197 end=4.819238 rc=0','kind=1 begin=4.819197 end=4.819238 rc=-1'))['accepted'])
if __name__=='__main__':unittest.main()
