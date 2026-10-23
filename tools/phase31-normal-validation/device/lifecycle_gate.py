"""用同一会话真实 Ability/窗口/Surface 事件与配对采样核对恢复。"""
import re,json,math
from timeline_gate import analyze as timeline
def analyze_background(text,rows):
 problems=[];structure=timeline(rows)
 if not structure['complete'] or not structure['coverageComplete']:problems.append('timeline_incomplete')
 try:
  rows=sorted(rows,key=lambda r:r['seq']);bg=[r for r in rows if r['event']=='ability_background']
  if len(bg)!=1:return {'accepted':False,'problems':problems+['background_count']}
  b=bg[0]['monoNs'];fg=next((r['monoNs'] for r in rows if r['event']=='ability_foreground' and r['monoNs']>b),None)
  if fg is None:return {'accepted':False,'problems':problems+['missing_foreground']}
  if fg-b<3000000000:problems.append('background_under_3s')
  for event,lo,hi in [('window_inactive',b-1000000000,b+1000000000),('stage_hidden',b-1000000000,b+1000000000),('window_active',fg,fg+1000000000),('stage_shown',fg,fg+1000000000)]:
   if not any(r['event']==event and lo<=r['monoNs']<=hi for r in rows):problems.append('missing_'+event)
  if any(r['event'] in ('surface_destroy','stage_destroy','ability_destroy') for r in rows) or sum(r['event']=='surface_create' for r in rows)!=1:problems.append('surface_or_ability_recreated')
  if len(re.findall(r'^P24_FILE_LOADED ',text,re.M))!=1:problems.append('player_reloaded')
  obs=[json.loads(l[16:]) for l in text.splitlines() if l.startswith('P24_OBSERVATION ')];samples=[r for r in rows if r['event']=='sample_begin']
  if any(o['time-pos']['rc']==0 and (type(o['time-pos']['value']) not in (int,float) or not math.isfinite(o['time-pos']['value'])) for o in obs):problems.append('nonfinite_pts')
  if len(samples)!=len(obs):problems.append('sample_alignment')
  aligned=list(zip(samples,obs));valid=lambda o:o['time-pos']['rc']==0 and o['videoSampleRc']==0 and isinstance(o['time-pos']['value'],(int,float)) and math.isfinite(o['time-pos']['value'])
  after=[(r,o) for r,o in aligned if fg<=r['monoNs']<=fg+15000000000 and valid(o)]
  if not after or after[-1][1]['time-pos']['value']-after[0][1]['time-pos']['value']<3:problems.append('foreground_progress')
  pid=int(re.search(r'^P24_BEGIN .* pid=(\d+)',text,re.M)[1]);session_begin=next(r for r in rows if r['event']=='session_begin')
  if session_begin['rc']!=pid:problems.append('pid_mismatch')
  return {'accepted':not problems,'problems':problems,'pid':pid,'session':session_begin['session'],'backgroundSeconds':(fg-b)/1e9,'firstForegroundSampleDelay':(after[0][0]['monoNs']-fg)/1e9 if after else None,'foregroundProgress':after[-1][1]['time-pos']['value']-after[0][1]['time-pos']['value'] if after else None,'sameSessionRecovery':not problems}
 except (ValueError,TypeError,KeyError,IndexError,StopIteration) as e:return {'accepted':False,'problems':problems+['malformed_'+type(e).__name__]}
