import sys,json,unittest,os
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'device'));from lifecycle_gate import analyze_background
F=json.loads((Path(__file__).parent/'fixtures/background.json').read_text());TEXT=F['text'];ROWS=F['rows']
if 'PHASE31_RAW_EVIDENCE' in os.environ:
 P=Path(os.environ['PHASE31_RAW_EVIDENCE'])/'device-background-01';TEXT=(P/'vk-background-0.log').read_text();ROWS=[]
 for p in P.glob('timeline-*.jsonl'):ROWS.extend(json.loads(l) for l in p.read_text().splitlines())
class Lifecycle(unittest.TestCase):
 def test_single_nan_pts(self):
  lines=TEXT.splitlines()
  for i,l in enumerate(lines):
   if l.startswith('P24_OBSERVATION '):
    d=json.loads(l[16:])
    if d['time-pos']['rc']==0:d['time-pos']['value']=float('nan');lines[i]='P24_OBSERVATION '+json.dumps(d);break
  self.assertFalse(analyze_background('\n'.join(lines),ROWS)['accepted'])
 def test_real(self):self.assertTrue(analyze_background(TEXT,ROWS)['accepted'])
 def test_short_background(self):
  import copy
  rows=copy.deepcopy(ROWS);bg=next(r for r in rows if r['event']=='ability_background')['monoNs'];fg=min(r['monoNs'] for r in rows if r['event']=='ability_foreground' and r['monoNs']>bg);shift=fg-bg-2000000000
  for r in rows:
   if r['event'] in ('ability_background','window_inactive','stage_hidden','stage_paused'):r['monoNs']+=shift;r['wallNs']+=shift
  self.assertFalse(analyze_background(TEXT,rows)['accepted'])
 def test_nonfinite_pts(self):
  lines=[]
  for l in TEXT.splitlines():
   if l.startswith('P24_OBSERVATION '):
    d=json.loads(l[16:]);d['time-pos']={'rc':0,'value':float('nan')};l='P24_OBSERVATION '+json.dumps(d)
   lines.append(l)
  self.assertFalse(analyze_background('\n'.join(lines),ROWS)['accepted'])
 def test_no_focus(self):self.assertFalse(analyze_background(TEXT,[r for r in ROWS if r['event']!='window_inactive'])['accepted'])
 def test_surface_recreated(self):
  row=dict(next(r for r in ROWS if r['event']=='ability_background'));row['event']='surface_destroy';self.assertFalse(analyze_background(TEXT,ROWS+[row])['accepted'])
 def test_reloaded(self):self.assertFalse(analyze_background(TEXT+'\nP24_FILE_LOADED index=0',ROWS)['accepted'])
if __name__=='__main__':unittest.main()
