import sys,unittest,json,os
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'device'));from playback_gate import analyze
R=Path(__file__).resolve().parents[1]
SW=(Path(os.environ['PHASE31_RAW_EVIDENCE'])/'device-switch-01/vk-switch-normal-0.log' if 'PHASE31_RAW_EVIDENCE' in os.environ else Path(__file__).parent/'fixtures/switch.log').read_text()
def long_text():
 rows=['P24_LOAD sample=nas-media-01 index=0','P24_FILE_LOADED index=0']
 for t in range(0,3606,5):
  d={'t':t,'fileIndex':0,'videoSampleRc':0,'hwdec':'ohcodec','ao':'ohaudio','gpu':'ohosvk','time-pos':{'rc':0,'value':t},'speed':{'rc':0,'value':1},'paused-for-cache':{'rc':0,'value':False}}
  rows.append('P24_OBSERVATION '+json.dumps(d))
 rows.append('P24_RESULT loaded=1 eof=0 errors=0 continuousSeconds=3605 continuousPassed=1 reason=none stopped=0')
 return '\n'.join(rows)
class Playback(unittest.TestCase):
 def test_missing_switch_restart(self):self.assertFalse(analyze('\n'.join(l for l in SW.splitlines() if not l.startswith('P24_PLAYBACK_RESTART ')),'vk-switch-normal')['accepted'])
 def test_wrong_switch_end(self):self.assertFalse(analyze(SW.replace('P24_END reason=2 error=0','P24_END reason=4 error=-1',1),'vk-switch-normal')['accepted'])
 def test_spec_10s_media_wall_tolerance(self):
  lines=[]
  for l in long_text().splitlines():
   if l.startswith('P24_OBSERVATION '):
    d=json.loads(l[16:]);d['time-pos']['value']*=1+7/3605;l='P24_OBSERVATION '+json.dumps(d)
   lines.append(l)
  self.assertTrue(analyze('\n'.join(lines),'vk-nas-long')['accepted'])
 def test_nan_time(self):
  lines=[]
  for l in long_text().splitlines():
   if l.startswith('P24_OBSERVATION '):
    d=json.loads(l[16:]);d['t']=float('nan');l='P24_OBSERVATION '+json.dumps(d)
   lines.append(l)
  self.assertFalse(analyze('\n'.join(lines),'vk-nas-long')['accepted'])
 def test_long_eof(self):self.assertFalse(analyze(long_text().replace('eof=0','eof=1'),'vk-nas-long')['accepted'])
 def test_duplicate_result(self):self.assertFalse(analyze(long_text().replace('errors=0','errors=0 errors=1'),'vk-nas-long')['accepted'])
 def test_stopped_01(self):self.assertFalse(analyze(long_text().replace('stopped=0','stopped=01'),'vk-nas-long')['accepted'])
 def test_switch_under_3s(self):
  lines=[];seen=set()
  for l in SW.splitlines():
   if l.startswith('P24_OBSERVATION '):
    d=json.loads(l[16:]);idx=d['fileIndex']
    if idx not in seen and d['time-pos']['rc']==0:d['time-pos']['value']+=.5;seen.add(idx)
    l='P24_OBSERVATION '+json.dumps(d)
   lines.append(l)
  self.assertFalse(analyze('\n'.join(lines),'vk-switch-normal')['accepted'])
 def test_switch(self):self.assertTrue(analyze(SW,'vk-switch-normal')['accepted'])
 def test_missing_generation(self):self.assertFalse(analyze(SW.replace('P24_FILE_LOADED index=1','missing'),'vk-switch-normal')['accepted'])
 def test_long(self):self.assertTrue(analyze(long_text(),'vk-nas-long')['accepted'])
 def test_gap(self):self.assertFalse(analyze('\n'.join(l for l in long_text().splitlines() if not(l.startswith('P24_OBSERVATION ') and 100<json.loads(l[16:])['t']<130)),'vk-nas-long')['accepted'])
 def test_short(self):self.assertFalse(analyze(long_text().replace('3605','3500'),'vk-nas-long')['accepted'])
 def test_seek_in_long(self):self.assertFalse(analyze(long_text()+'\nP24_SEEK t=10','vk-nas-long')['accepted'])
 def test_wrong_speed(self):self.assertFalse(analyze(long_text().replace('"value": 1}', '"value": 2}'),'vk-nas-long')['accepted'])
if __name__=='__main__':unittest.main()
