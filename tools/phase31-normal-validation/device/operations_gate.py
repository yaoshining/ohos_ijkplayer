"""独立检查原始操作证据，不信任控制器 PASS 文本。"""
import re,json,math
from result_fields import parse as parse_result
def analyze(text):
 problems=[];samples=[];events={'SEEK':[],'PLAYBACK_RESTART':[]};actions=[]
 try:
  for line in text.splitlines():
   if line.startswith('P31_SAMPLE '):samples.append(json.loads(line[11:]))
   m=re.fullmatch(r'P31_ACTION kind=(\d+) begin=([\d.]+) end=([\d.]+) rc=(-?\d+)',line)
   if m:actions.append(dict(zip(('kind','begin','end','rc'),(int(m[1]),float(m[2]),float(m[3]),int(m[4])))))
   for k in events:
    m=re.fullmatch('P24_'+k+r' t=([\d.]+)',line)
    if m:events[k].append(float(m[1]))
  if any(type(s.get('t')) not in (int,float) or not math.isfinite(s['t']) or s['t']<0 or (s.get('ptsRc')==0 and (type(s.get('pts')) not in (int,float) or not math.isfinite(s['pts']))) for s in samples):return {'accepted':False,'problems':['nonfinite_sample']}
  if len(samples)<2 or any(b['t']<=a['t'] for a,b in zip(samples,samples[1:])):problems.append('sample_time')
  if [a['kind'] for a in actions]!=[1,2,3,4]:problems.append('action_sequence')
  if any(a['rc']!=0 or a['end']<a['begin'] for a in actions):problems.append('action_failure')
  if problems:return {'accepted':False,'problems':problems}
  a1,pa,resume_action,a4=actions
  if not all(b['begin']>a['end'] for a,b in zip(actions,actions[1:])):problems.append('action_time')
  valid=lambda s:s['ptsRc']==0 and isinstance(s['pts'],(int,float)) and math.isfinite(s['pts'])
  targets=[]
  for act,target,stop in ((a1,30,pa['begin']),(a4,5,samples[-1]['t']+.001)):
   seeks=[t for t in events['SEEK'] if act['end']<=t<=min(stop,act['end']+15)]
   restarts=[t for t in events['PLAYBACK_RESTART'] if seeks and seeks[0]<=t<=min(stop,act['end']+15)]
   hit=next((s for s in samples if restarts and restarts[0]<=s['t']<=min(stop,act['end']+15) and valid(s) and abs(s['pts']-target)<=2),None)
   if hit is None:problems.append('seek_events_or_target');continue
   progress=[s for s in samples if hit['t']<s['t']<=stop and valid(s) and s['pts']>=hit['pts']+3]
   if not progress:problems.append('seek_progress')
   targets.append({'target':target,'observed':hit['pts'],'latency':hit['t']-act['end']})
  window=[s for s in samples if pa['end']<=s['t']<=resume_action['begin']]
  start=next((i for i,s in enumerate(window) if valid(s) and s['pauseRc']==0 and s['pause']==1),None)
  pause=window[start:] if start is not None else []
  if not pause or pause[-1]['t']-pause[0]['t']<3 or any(not valid(s) or s['pauseRc']!=0 or s['pause']!=1 or abs(s['pts']-pause[0]['pts'])>.25 for s in pause) or any(b['t']-a['t']>.5 for a,b in zip(pause,pause[1:])):problems.append('pause_not_continuous')
  resume=[s for s in samples if resume_action['end']<=s['t']<=a4['begin'] and valid(s) and s['pauseRc']==0 and s['pause']==0]
  if not pause or not resume or resume[-1]['pts']-pause[-1]['pts']<3:problems.append('resume_progress')
  if not re_full_result(text):problems.append('result_not_success')
  return {'accepted':not problems,'problems':problems,'targets':targets,'pauseSeconds':pause[-1]['t']-pause[0]['t'] if pause else None,'samples':len(samples)}
 except (ValueError,TypeError,KeyError,IndexError) as e:return {'accepted':False,'problems':['malformed_'+type(e).__name__]}
def re_full_result(text):
 result=parse_result(text)
 return result['errors']==0 and result['stopped']==0 and result['eof']==0 and result['loaded']==1 and result.get('operationsPassed')==1 and result.get('reason')=='none'
