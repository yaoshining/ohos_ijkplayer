"""长播与切换的观测门禁；不替代时间线、库身份与清理门禁。"""
import json,re,math
from result_fields import parse as parse_result
def analyze(text,mode):
 problems=[]
 try:
  obs=[json.loads(l[16:]) for l in text.splitlines() if l.startswith('P24_OBSERVATION ')]
  loaded=[int(x) for x in re.findall(r'^P24_FILE_LOADED index=(\d+)$',text,re.M)]
  result=parse_result(text)
  if result['errors']!=0 or result['stopped']!=0 or result.get('reason')!='none':problems.append('result')
  if any(type(r.get('t')) not in (int,float) or not math.isfinite(r['t']) or r['t']<0 for r in obs):return {'accepted':False,'problems':['invalid_sample_time']}
  if not obs or any(b['t']<=a['t'] for a,b in zip(obs,obs[1:])):problems.append('monotonic_samples')
  valid=lambda r:r['time-pos']['rc']==0 and isinstance(r['time-pos']['value'],(float,int)) and math.isfinite(r['time-pos']['value']) and r['videoSampleRc']==0
  good=[r for r in obs if valid(r)]
  if not good:return {'accepted':False,'problems':problems+['no_valid_pts']}
  if any(r['hwdec']!='ohcodec' or r['gpu']!='ohosvk' for r in good):problems.append('hardware_route')
  if mode=='vk-switch-normal':
   if result['loaded']!=3 or result['eof']!=0:problems.append('switch_result')
   if loaded!=[0,1,2]:problems.append('load_generations')
   loads=[int(i) for i in re.findall(r'^P24_LOAD sample=[a-z0-9-]+ index=(\d+)$',text,re.M)]
   ends=[(int(a),int(b)) for a,b in re.findall(r'^P24_END reason=(-?\d+) error=(-?\d+)$',text,re.M)]
   replacements=[int(i) for i in re.findall(r'^P31_EXPECTED_REPLACEMENT index=(\d+)$',text,re.M)]
   if loads!=[0,1,2] or ends!=[(2,0),(2,0)] or replacements!=[1,2]:problems.append('switch_transition_events')
   current=-1;pending=-1;restarted=set()
   for line in text.splitlines():
    lm=re.fullmatch(r'P24_LOAD sample=[a-z0-9-]+ index=(\d+)',line);fm=re.fullmatch(r'P24_FILE_LOADED index=(\d+)',line);rm=re.fullmatch(r'P24_PLAYBACK_RESTART t=([0-9.]+)',line)
    if lm:pending=int(lm[1])
    if fm:
     current=int(fm[1])
     if current!=pending:problems.append('load_event_order')
    if rm and current==pending and current>=0:restarted.add(current)
   if restarted!={0,1,2}:problems.append('missing_generation_restart')
   for i in range(3):
    group=[r for r in good if r['fileIndex']==i]
    if len(group)<2 or group[-1]['time-pos']['value']<3 or group[-1]['time-pos']['value']-group[0]['time-pos']['value']<3:problems.append('generation_progress_'+str(i))
   return {'accepted':not problems,'problems':problems,'loaded':loaded,'validSamples':len(good)}
  if mode!='vk-nas-long':return {'accepted':False,'problems':['unsupported_mode']}
  if result['loaded']!=1 or result['eof']!=0 or result.get('continuousPassed')!=1 or result.get('continuousSeconds',0)<3600:problems.append('long_result')
  start=obs.index(good[0]);window=obs[start:]
  if loaded!=[0] or any(r['fileIndex']!=0 for r in window):problems.append('single_source')
  if re.search(r'^P24_SEEK|^P31_ACTION',text,re.M):problems.append('operation_during_continuity')
  if any(not valid(r) for r in window):problems.append('invalid_inside_window')
  if any(r['speed']!={'rc':0,'value':1} or r['paused-for-cache']!={'rc':0,'value':False} or r['ao']!='ohaudio' for r in window):problems.append('playback_state')
  span=window[-1]['t']-window[0]['t'];gaps=[b['t']-a['t'] for a,b in zip(window,window[1:])]
  if span<3600:problems.append('duration_under_3600')
  if not gaps or max(gaps)>15:problems.append('sample_gap')
  pts=[r['time-pos']['value'] for r in window if valid(r)]
  if any(b<=a for a,b in zip(pts,pts[1:])) or pts[-1]-pts[0]<3600:problems.append('pts_continuity')
  if abs((pts[-1]-pts[0])-span)>10:problems.append('pts_wall_disagreement')
  return {'accepted':not problems,'problems':problems,'continuousWallSeconds':span,'ptsProgressSeconds':pts[-1]-pts[0],'maxSampleGapSeconds':max(gaps,default=None),'validSamples':len(good),'oldGapRootCauseResolved':False,'leakFreeClaim':False}
 except (ValueError,TypeError,KeyError,IndexError) as e:return {'accepted':False,'problems':['malformed_'+type(e).__name__]}
