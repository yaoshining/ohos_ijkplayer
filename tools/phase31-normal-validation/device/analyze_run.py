"""组合独立门禁；输入仅本地证据，不访问设备。不把原始native消息缺失当无警告。"""
from result_fields import parse as parse_result
from pathlib import Path
import argparse,json,re
from timeline_gate import read_lanes,analyze as timeline
from identity_gate import analyze as identity
from operations_gate import analyze as operations
from playback_gate import analyze as playback
from lifecycle_gate import analyze_background
from close_gate import analyze as close
from cleanup_gate import derive_cleanup
from run import cleanup_pass

def analyze(directory,binding):
 p=Path(directory);summary=json.loads((p/'summary.json').read_text());mode=summary['mode'];logs=list(p.glob(mode+'-[0-9]*.log'));logs=[f for f in logs if not f.name.endswith('-native.log')]
 if len(logs)!=1:return {'accepted':False,'problems':['run_log_count']}
 text=logs[0].read_text();rows,errors=read_lanes(list(p.glob('timeline-*.jsonl')));tl=timeline(rows,errors);ident=identity(text,rows,summary.get('pids',[]),binding)
 problems=[]
 if summary.get('outcome')!='result-recorded' or summary.get('executionError') or summary.get('collectionError'):problems.append('collection_incomplete')
 if not tl['complete'] or not tl.get('coverageComplete'):problems.append('timeline_incomplete')
 if not ident['accepted']:problems.append('identity')
 rs=re.findall(r'^P24_RESULT (.*)$',text,re.M)
 try:
  result_fields=parse_result(text)
  if len(rs)!=1 or rs[0].strip()!=summary['result'].strip() or result_fields['errors']!=0 or result_fields['stopped']!=0:problems.append('result')
 except ValueError:problems.append('result')
 off=[r for r in rows if r['event']=='keep_awake_readback' and r['key']==0 and r['rc']==0]
 if not off:problems.append('keep_screen_release')
 detail={}
 if mode=='vk-close':
  detail=close(json.loads((p/'normal-close-request.json').read_text()),json.loads((p/'before-cleanup.json').read_text()),rows)
 elif mode=='vk-nas-ops':detail=operations(text)
 elif mode=='vk-background':detail=analyze_background(text,rows)
 elif mode in ('vk-switch-normal','vk-nas-long'):
  detail=playback(text,mode)
  if mode=='vk-nas-long' and not tl['continuousEligible']:problems.append('timeline_not_continuous')
 else:
  obs=[json.loads(l[16:]) for l in text.splitlines() if l.startswith('P24_OBSERVATION ')];good=[r for r in obs if r['time-pos']['rc']==0 and r['videoSampleRc']==0]
  detail={'accepted':len(good)>=2 and all(r['hwdec']=='ohcodec' and r['gpu']=='ohosvk' for r in good),'validSamples':len(good),'claim':'短冒烟；不代替双向seek或长播'}
 if not detail.get('accepted'):problems.append('scenario')
 cleanup=None
 if not summary.get('keptProcess'):
  checks,_=derive_cleanup(json.loads((p/'commands.json').read_text()));cleanup=cleanup_pass(checks)
  if not cleanup:problems.append('external_cleanup')
 elif mode!='vk-close':problems.append('unexpected_kept_process')
 return {'accepted':not problems,'problems':problems,'mode':mode,'identity':ident,'scenario':detail,'timeline':tl,'externalCleanupAccepted':cleanup,'formalArtifactAllowed':False,'physicalAVConfirmed':False,'oldGapRootCauseResolved':False,'nativeWarningFreeClaim':False}
if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('directory',type=Path);ap.add_argument('--binding',required=True,type=Path);a=ap.parse_args();r=analyze(a.directory,json.loads(a.binding.read_text()));(a.directory/'acceptance.json').write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n');print(json.dumps({'accepted':r['accepted'],'problems':r['problems'],'mode':r.get('mode')}));raise SystemExit(0 if r['accepted'] else 1)
