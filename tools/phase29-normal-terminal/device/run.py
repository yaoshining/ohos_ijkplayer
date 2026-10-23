from pathlib import Path
import subprocess,json,time,datetime,argparse,re
import cleanup_gate as gate
H='/Applications/DevEco-Studio.app/Contents/sdk/default/openharmony/toolchains/hdc';T='192.168.3.85:5555';B='com.yaoshining.phase22probe';BASE='/data/app/el2/100/base/'+B+'/haps/entry/files/phase29-terminal';LOGICAL='/data/storage/el2/base/haps/entry/files/phase29-terminal'
p=argparse.ArgumentParser();p.add_argument('--mode',required=True);p.add_argument('--variant',choices=['normal','fault'],required=True);p.add_argument('--out',type=Path,required=True);p.add_argument('--seconds',type=int,default=75);a=p.parse_args();out=a.out;out.mkdir(parents=True,exist_ok=False);rows=[]
allowed={'vk-pq','normal-repeat','no-registration','gl-pq','gl-pq-sw','vk-inject-wait','vk-inject-release','callback-hang','ui-block','logger-hang'};assert a.mode in allowed
fatal=a.mode in {'vk-inject-wait','callback-hang','ui-block','logger-hang'}
def call(args,required=False,limit=15):
 cmd=[H,'-t',T,*args];t=time.monotonic();d={'command':cmd,'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'monotonic':t}
 try:p=subprocess.run(cmd,capture_output=True,text=True,timeout=limit);d.update(exit=p.returncode,stdout=p.stdout,stderr=p.stderr)
 except subprocess.TimeoutExpired as e:d.update(exit=124,timeout=limit,stdout=str(e.stdout or ''),stderr=str(e.stderr or ''))
 d['elapsed']=time.monotonic()-t;rows.append(d);(out/'commands.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2))
 if required and not gate.valid_command(d):raise RuntimeError(d)
 return d
call(['list','targets','-v'],True);call(['shell','aa','force-stop',B],True);before=call(['shell','pidof',B]);assert gate.valid_pid_absent(before)
# Only this newly created test root. Preserve each earlier run locally before reuse.
call(['shell','mkdir','-p',BASE],True)
listing=call(['shell','ls',BASE],True)
for n in listing['stdout'].split():
 if re.fullmatch(r'[A-Za-z0-9_.-]+',n) and (n.endswith('.log') or n.endswith('-result.txt') or n.startswith('timeline-') or n=='admission-result.json'):call(['shell','rm',BASE+'/'+n],True)
def fetch_private(name):
 path=out/('live-'+name)
 d=call(['file','recv','-b',B,LOGICAL+'/'+name,str(path.resolve())])
 return path.read_text(errors='replace') if gate.valid_command(d) and path.is_file() else ''
system_file=(out/'system-live.log').open('wb')
system_cmd=[H,'-t',T,'shell','hilog','-v','monotonic','-e',B]
system_proc=subprocess.Popen(system_cmd,stdout=system_file,stderr=subprocess.STDOUT)
started=time.monotonic();s=call(['shell','aa','start','-b',B,'-a','EntryAbility','--ps','phase29Mode',a.mode],True);assert 'start ability successfully' in s['stdout'];pids=[];spontaneous=False;outcome='deadline';seen_terminal_at=None;result='';exited_at=None
try:
 while time.monotonic()-started<a.seconds:
  pid=call(['shell','pidof',B]);assert gate.valid_command(pid,(0,1)),pid
  v=pid['stdout'].strip()
  if v and v not in pids:pids.append(v)
  if not v and pids:spontaneous=True;exited_at=time.monotonic();outcome='app-exited';break
  # timestamp source in app monotonic log; log absence is not success.
  log=fetch_private('terminal-events.log')
  if 'event=terminal-ready' in log and seen_terminal_at is None:
   seen_terminal_at=time.monotonic()
   if a.mode=='vk-inject-wait':
    shot='/data/local/tmp/phase29-terminal-shot.jpeg'
    call(['shell','snapshot_display','-f',shot],limit=5)
    call(['file','recv',shot,str((out/'terminal-shot.jpeg').resolve())],limit=5)
  if fatal and seen_terminal_at and time.monotonic()-seen_terminal_at>5:outcome='terminal-deadline-exceeded';break
  if not fatal:
   rs=call(['shell','cat',BASE+'/vk-pq-result.txt']) if a.mode=='normal-repeat' else call(['shell','cat',BASE+'/'+a.mode+'-result.txt'])
   names=call(['shell','ls',BASE])
   timelines=[n for n in names['stdout'].split() if re.fullmatch(r'timeline-[A-Za-z0-9_-]+-ui\.jsonl',n)]
   tl=''.join(fetch_private(n) for n in timelines)
   if 'session_end' in tl:outcome='normal-session-end';result=rs['stdout'];break
  time.sleep(.2)
 # Query app absence BEFORE any cleanup force-stop for fatal cases.
 pre_cleanup={'pid':call(['shell','pidof',B]),'ability':call(['shell','aa','dump','-a']),'window':call(['shell','hidumper','-s','WindowManagerService','-a','-a']),'targets':call(['list','targets','-v'])}
 (out/'before-cleanup.json').write_text(json.dumps(pre_cleanup,ensure_ascii=False,indent=2))
finally:
 system_proc.terminate()
 try:system_exit=system_proc.wait(timeout=3)
 except subprocess.TimeoutExpired:system_proc.kill();system_exit=system_proc.wait(timeout=3)
 system_file.close()
 (out/'system-live-command.json').write_text(json.dumps({'command':system_cmd,'collectorExit':system_exit,'stoppedBeforeExternalCleanup':True},indent=2))
 call(['shell','aa','force-stop',B]);call(['shell','pidof',B]);call(['shell','hidumper','-s','WindowManagerService','-a','-a']);call(['shell','aa','dump','-a']);call(['list','targets','-v'])
 checks,detail=gate.derive_cleanup(rows,B);(out/'cleanup.json').write_text(json.dumps({'checks':checks,'detail':detail},ensure_ascii=False,indent=2))
listing=call(['shell','ls',BASE],True)
for n in listing['stdout'].split():
 if re.fullmatch(r'[A-Za-z0-9_.-]+',n) and (n.endswith(('.log','.json','.jsonl')) or n.endswith('-result.txt') or n=='run-plan.txt'):
  call(['file','recv','-b',B,LOGICAL+'/'+n,str((out/n).resolve())],limit=20)
res={'mode':a.mode,'variant':a.variant,'pids':pids,'outcome':outcome,'spontaneousExitBeforeForceStop':spontaneous,'elapsedToExit':exited_at-started if exited_at else None,'firstTerminalObservedToExit':exited_at-seen_terminal_at if exited_at and seen_terminal_at else None,'result':result,'cleanupEvidenceValid':checks['cleanupEvidenceValid'],'formalArtifactAllowed':False,'analysisPending':True};(out/'summary.json').write_text(json.dumps(res,ensure_ascii=False,indent=2));print(json.dumps(res,ensure_ascii=False))
