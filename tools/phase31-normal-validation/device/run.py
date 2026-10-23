"""Phase31有界设备采集；只控制独立bundle，私有配置不进入日志/采集。"""
from pathlib import Path
import subprocess,json,time,datetime,argparse,re,sys
import cleanup_gate as gate
from completion_gate import completed
H='/Applications/DevEco-Studio.app/Contents/sdk/default/openharmony/toolchains/hdc';T='192.168.3.85:5555';B='com.yaoshining.phase22probe';BASE='/data/app/el2/100/base/'+B+'/haps/entry/files/phase31-normal';LOGICAL='/data/storage/el2/base/haps/entry/files/phase31-normal'
ALLOWED={'vk-nas-short','vk-nas-long','vk-nas-ops','vk-switch-normal','vk-background','vk-close','vk-pq'}
def cleanup_pass(checks):return checks.get('cleanupEvidenceValid') is True and checks.get('abilityAbsent') is True and checks.get('windowAbsent') is True and checks.get('pidAbsent') is True
def main():
 p=argparse.ArgumentParser();p.add_argument('--mode',required=True,choices=sorted(ALLOWED));p.add_argument('--out',type=Path,required=True);p.add_argument('--no-start-stop',action='store_true');p.add_argument('--keep-process',action='store_true');a=p.parse_args();out=a.out;out.mkdir(parents=True,exist_ok=False);rows=[]
 def call(args,required=False,limit=15):
  cmd=[H,'-t',T,*args];t=time.monotonic();d={'command':cmd,'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'monotonic':t}
  try:q=subprocess.run(cmd,capture_output=True,text=True,timeout=limit);d.update(exit=q.returncode,stdout=q.stdout,stderr=q.stderr)
  except subprocess.TimeoutExpired as e:d.update(exit=124,timeout=limit,stdout=(e.stdout or b'').decode(errors='replace') if isinstance(e.stdout,bytes) else e.stdout or '',stderr=(e.stderr or b'').decode(errors='replace') if isinstance(e.stderr,bytes) else e.stderr or '')
  d['elapsed']=time.monotonic()-t;rows.append(d);(out/'commands.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2))
  if required and not gate.valid_command(d):raise RuntimeError('device command failed: '+str(args[:3]))
  return d
 connected=call(['list','targets','-v'],True)
 if not gate.target_connected(connected):raise RuntimeError('target not Connected')
 started=time.monotonic();pids=[];outcome='deadline';backgroundAt=None;foregroundAt=None;deadline=3900 if a.mode=='vk-nas-long' else 150;result='';runlog='';runname=None;cleanup=None;collectionError=None
 try:
  if not a.no_start_stop:
   stop=call(['shell','aa','force-stop',B],True)
   if 'force stop process successfully' not in stop['stdout'] or not gate.valid_pid_absent(call(['shell','pidof',B])):raise RuntimeError('initial stop failed')
  call(['shell','mkdir','-p',BASE],True)
  listing=call(['shell','ls',BASE],True)
  for n in listing['stdout'].split():
   if re.fullmatch(r'[A-Za-z0-9_.-]+',n) and (n.endswith(('.log','.jsonl','-result.txt')) or n in ('normal-close-request.json','run-plan.txt')):call(['shell','rm',BASE+'/'+n],True)
  started=time.monotonic();s=call(['shell','aa','start','-b',B,'-a','EntryAbility','--ps','phase31Mode',a.mode],True)
  if 'start ability successfully' not in s['stdout']:raise RuntimeError('start not acknowledged')
  while time.monotonic()-started<deadline:
   pid=call(['shell','pidof',B]);
   if not gate.valid_command(pid,(0,1)):raise RuntimeError('pid query invalid')
   v=pid['stdout'].strip()
   if v and v not in pids:pids.append(v)
   names=call(['shell','ls',BASE],True)['stdout'].split();rn=[n for n in names if re.fullmatch(re.escape(a.mode)+r'-[0-9]+\.log',n)]
   if rn:
    runname=rn[-1];read=call(['shell','tail','-n','10',BASE+'/'+runname]);runlog=read['stdout'] if gate.valid_command(read) else ''
    if a.mode=='vk-background' and backgroundAt is None and 'P24_OBSERVATION' in runlog and '"time-pos":{"rc":0' in runlog and time.monotonic()-started>8:
     call(['shell','uitest','uiInput','keyEvent','Home'],True);backgroundAt=time.monotonic();call(['shell','aa','dump','-a']);call(['shell','hidumper','-s','WindowManagerService','-a','-a'])
    if a.mode=='vk-background' and backgroundAt is not None and foregroundAt is None and time.monotonic()-backgroundAt>=4:
     call(['shell','aa','start','-b',B,'-a','EntryAbility'],True);foregroundAt=time.monotonic()
   rs=call(['shell','cat',BASE+'/'+a.mode+'-result.txt'])
   if gate.valid_command(rs) and rs['stdout'].strip():
    full=call(['shell','cat',BASE+'/'+runname]) if runname else {}
    if completed(a.mode,rs,full.get('stdout','')):
     result=rs['stdout'];outcome='result-recorded';time.sleep(2);break
    outcome='invalid-result';break
   if not v and pids:outcome='process-exited-before-result';break
   if a.mode=='vk-nas-long':
    (out/'progress.json').write_text(json.dumps({'elapsed':time.monotonic()-started,'pid':v,'tail':runlog,'atUTC':datetime.datetime.now(datetime.timezone.utc).isoformat()},ensure_ascii=False,indent=2))
   time.sleep(10 if a.mode=='vk-nas-long' else .5)
 finally:
  originalError=sys.exc_info()[1]
  try:
   before={'pid':call(['shell','pidof',B]),'ability':call(['shell','aa','dump','-a']),'window':call(['shell','hidumper','-s','WindowManagerService','-a','-a']),'targets':call(['list','targets','-v'])};(out/'before-cleanup.json').write_text(json.dumps(before,ensure_ascii=False,indent=2))
   names=call(['shell','ls',BASE],True)['stdout'].split()
   for n in names:
    if re.fullmatch(r'(timeline-[a-f0-9-]+-(ui|worker|heartbeat)\.jsonl|vk-[a-z-]+-[0-9]+(?:-native)?\.log|vk-[a-z-]+-result\.txt|maps\.txt|normal-close-request\.json|terminal-events\.log)',n):
     if 'nas' in a.mode and n.endswith('-native.log'):continue
     d=call(['file','recv','-b',B,LOGICAL+'/'+n,str((out/n).resolve())],limit=30)
     if not gate.valid_command(d) or 'FileTransfer finish' not in d['stdout'] or not (out/n).is_file():raise RuntimeError('file collection failed')
  except Exception as error:
   collectionError=error
   (out/'collection-error.json').write_text(json.dumps({'type':type(error).__name__,'message':str(error)},ensure_ascii=False,indent=2))
  finally:
   kept=a.keep_process and originalError is None and collectionError is None and outcome=='result-recorded'
   if not kept:
    call(['shell','aa','force-stop',B]);call(['shell','pidof',B]);call(['shell','hidumper','-s','WindowManagerService','-a','-a']);call(['shell','aa','dump','-a']);call(['list','targets','-v']);checks,detail=gate.derive_cleanup(rows,B);cleanup=cleanup_pass(checks);(out/'cleanup.json').write_text(json.dumps({'accepted':cleanup,'checks':checks,'detail':detail},ensure_ascii=False,indent=2))
   res={'mode':a.mode,'pids':pids,'outcome':outcome,'elapsed':time.monotonic()-started,'backgroundAt':backgroundAt,'foregroundAt':foregroundAt,'result':result,'cleanupAccepted':cleanup,'keptProcess':kept,'executionError':type(originalError).__name__ if originalError else None,'collectionError':type(collectionError).__name__ if collectionError else None,'formalArtifactAllowed':False,'analysisPending':True};(out/'summary.json').write_text(json.dumps(res,ensure_ascii=False,indent=2));print(json.dumps(res,ensure_ascii=False))
  if originalError is None and collectionError is not None:raise collectionError
 if outcome!='result-recorded' or cleanup is False:raise SystemExit(1)
if __name__=='__main__':main()
