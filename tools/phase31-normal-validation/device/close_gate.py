"""正常 terminateSelf 清理：cached PID允许，不把外部终止当自然退出。"""
from timeline_gate import analyze as timeline
from cleanup_gate import valid_command,target_connected,BUNDLE
def analyze(marker,before,rows):
 problems=[];ts=timeline(rows)
 if not ts['complete'] or not ts['coverageComplete']:problems.append('timeline_incomplete')
 if marker!={'requested':True,'cleanBeforeClose':True,'afterSessionEnd':True}:problems.append('close_marker')
 try:
  if not target_connected(before['targets']):problems.append('connection_unknown')
  ability=before['ability'];window=before['window'];pid=before['pid']
  if not valid_command(ability) or not any(x in ability['stdout'] for x in ('AbilityManagerService','current mission lists','AbilityRecord')) or BUNDLE in ability['stdout']:problems.append('ability_not_proven_absent')
  if not valid_command(window) or not any(x in window['stdout'] for x in ('WindowManagerService','Total window num')) or 'phase22probe' in window['stdout']:problems.append('window_not_proven_absent')
  if not valid_command(pid,(0,1)):problems.append('pid_query_invalid')
  ordered=sorted(rows,key=lambda r:r['seq']);destroy=[r for r in ordered if r['event']=='query_end' and r['generation']==103 and r['rc']==0];off=[r for r in ordered if r['event']=='keep_awake_readback' and r['key']==0 and r['rc']==0];end=[r for r in ordered if r['event']=='session_end' and r['rc']==0]
  if len(destroy)!=1 or not off or len(end)!=1 or not destroy[0]['seq']<off[-1]['seq']<end[0]['seq']:problems.append('cleanup_order')
  return {'accepted':not problems,'problems':problems,'classification':'normal_ability_close','cachedPidAfter':pid['stdout'].strip() or None,'session':ts.get('session')}
 except (KeyError,TypeError,IndexError) as e:return {'accepted':False,'problems':problems+['malformed_'+type(e).__name__]}
