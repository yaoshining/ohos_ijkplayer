"""按对应场景、PID和HAP判定；原始summary保持analysisPending，不覆盖。"""
from pathlib import Path
import json,re,hashlib
import cleanup_gate as gate
R=Path(__file__).resolve().parent.parent
B='com.yaoshining.phase22probe'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def text(p):return p.read_text(errors='replace') if p.exists() else ''
def analyze(name,hap,kind):
 d=R/'evidence'/name;s=json.loads((d/'summary.json').read_text());pid=s['pids'][0] if len(s['pids'])==1 else '';cmds=json.loads((d/'commands.json').read_text());artifact=json.loads((R/'artifacts'/hap).read_text());terminal=text(d/'terminal-events.log');native='\n'.join(text(p) for p in d.glob('*-native.log'));jobs=[p for p in d.glob('*.log') if re.fullmatch(r'(vk-[a-z-]+|callback-hang|ui-block|logger-hang)-\d+\.log',p.name)];ui='\n'.join(text(p) for p in d.glob('timeline-*-ui.jsonl'));worker='\n'.join(text(p) for p in d.glob('timeline-*-worker.jsonl'));system=text(d/'system-live.log');allrun=native+'\n'+'\n'.join(text(p) for p in jobs)
 cleanup,_=gate.derive_cleanup(cmds,B);checks={'singlePID':bool(pid),'collectorCleanupValid':cleanup['cleanupEvidenceValid'],'noRegistryAssertion':not re.search(r'Assertion failed|assertion failed|SIGABRT|SIGSEGV',allrun)}
 loaded={k:v for p in jobs for k,v in re.findall(r'loaded .*?/([^/ ]+) sha256=([0-9a-f]{64})',text(p))}
 if kind!='refused':checks['sevenMappedLibraries']=len(loaded)==7 and all(artifact['libraries'].get('libs/arm64-v8a/'+k)==v for k,v in loaded.items()) and all('mapped_expected_libraries=7 all_sha_match=1' in text(p) for p in jobs)
 detail={'hapSHA256':artifact['hapSHA256'],'jobs':[p.name for p in jobs],'loadedLibrarySHA256':loaded}
 if kind in ('normal','release','refused'):
  checks.update(sessionEnd='"event":"session_end"' in ui,keepScreenFalse=bool(re.search(r'"event":"keep_awake_readback","key":0',ui)),didNotSelfTerminate=not s['spontaneousExitBeforeForceStop'])
 if kind=='normal':
  checks['twoRealRunsSamePID']=len(jobs)==2 and len(re.findall(r'"event":"run_begin"',worker))==2 and all('pid='+pid+' ' in text(p) and 'eof=1 errors=0' in text(p) and 'P27_DESTROY_COMPLETE' in text(p) for p in jobs)
 elif kind=='release':
  checks.update(returnReplacement='stage=release kind=return-replacement real_called=1 real_rc=0 effective_rc=-1234' in native,surfaceRejected='OHCodec Surface is already terminal; refusing new producer' in native,codecDestroyed='op=destroy-close' in native,noProcessTerminal='event=terminal-ready' not in terminal,expectedRejectedSecondLoad=any('eof=1 errors=1' in text(p) for p in jobs));detail['expectedError']='第二片在terminal Surface上被拒绝，errors=1不是一般播放通过'
 elif kind=='refused':
  denial=json.loads((d/'admission-result.json').read_text());checks.update(explicitRefusal=denial=={'configured':False,'rejected':True,'fallbackAllowed':False,'mode':'no-registration'},sameRunOperator90=bool(re.search(r'"event":"operator_action","key":90',ui)),noRunOrLibrary=not jobs and '"event":"run_begin"' not in worker);detail['staleAdmissionElsewhere']='其他场景中残留admission-result.json不参与判定'
 else:
  pre=json.loads((d/'before-cleanup.json').read_text());checks.update(selfExitBeforeCleanup=s['spontaneousExitBeforeForceStop'],pidAbsentBeforeCleanup=gate.valid_pid_absent(pre['pid']),connected=gate.valid_command(pre['targets']) and bool(re.search(r'^192\.168\.3\.85:5555\s+TCP\s+Connected(?:\s|$)',pre['targets']['stdout'],re.M)),abilityQueryValid=gate.valid_command(pre['ability']) and any(x in pre['ability']['stdout'] for x in ('AbilityManagerService','current mission lists','AbilityRecord')),windowQueryValid=gate.valid_command(pre['window']) and any(x in pre['window']['stdout'] for x in ('WindowManagerService','Total window num')),noRemainingAbility=B not in pre['ability']['stdout'],noRemainingWindow='phase22probe' not in pre['window']['stdout'])
  exitrows=re.findall(r'^\s*(\d+\.\d+).*?'+re.escape(B)+r' with pid '+pid+r' exit with code:(\d+)',system,re.M);checks['systemPIDExitCode']=len(exitrows)==1 and int(exitrows[0][1])==(0 if kind=='ui' else 86)
  inject=re.findall(r'P28D_INJECT pid='+pid+r' stage=wait kind=return-replacement real_called=1 real_rc=0 effective_rc=-4 trigger=1',native);checks['realReturnReplacement']=len(inject)==1
  # Native P28_DRAIN time and app terminal use CLOCK_MONOTONIC. No host-observation shortcut.
  ready=re.findall(r'P29_APP t=(\d+) pid='+pid+r' event=terminal-ready code=-4',terminal)
  wait=re.findall(r'P28_DRAIN t=(\d+) op=queue-wait-idle rc=-4',native)
  startms=int(ready[0]) if len(ready)==1 else (int(wait[-1])/1000 if wait else None)
  elapsed=float(exitrows[0][0])*1000-startms if exitrows and startms else None;detail.update(deviceExitDeltaMs=elapsed,timeOrigin='first app snapshot' if ready else 'injected queue return; app logger intentionally blocked',exitRows=exitrows,hostObservationNotExact=s['firstTerminalObservedToExit'])
  marks={int(c):int(t) for t,c in re.findall(r'P29_APP t=(\d+) pid='+pid+r' event=ui code=(\d+)',terminal)}
  if kind=='ui':checks.update(uiOrder=all(x in marks for x in (1,2,3)) and startms<=marks[1]<=marks[2]<marks[3],beforeNativeDeadline=elapsed is not None and 0<elapsed<3000,screenshot=(d/'terminal-shot.jpeg').is_file());detail['screenshotSHA256']=sha(d/'terminal-shot.jpeg') if (d/'terminal-shot.jpeg').exists() else None
  else:checks['deadlineTolerance']=elapsed is not None and 2900<=elapsed<=3500;checks['noUIKillRequest']=3 not in marks
  if kind!='logger':checks['notificationOnce']=terminal.count('event=callback code=1')==1 and len(ready)==1
  detail['lifecycleMeaning']='异常主动终止或native deadline；不声明完整生命周期清理'
 return {'scenario':name,'kind':kind,'pid':pid,'checks':checks,'passed':all(checks.values()),**detail,'evidence':[{ 'file':str(p.relative_to(R)), 'sha256':sha(p)} for p in sorted(d.iterdir()) if p.is_file()]}
def main():
 rows=[analyze(*x) for x in [('device-normal-repeat-02','normal.json','normal'),('device-release-01','fault.json','release'),('device-no-registration-02','fault-ui2.json','refused'),('device-ui-fatal-03','fault-ui2.json','ui'),('device-callback-hang-02','fault-ui2.json','callback'),('device-ui-block-02','fault-ui2.json','ui-block'),('device-logger-hang-02','fault-ui2.json','logger')]]
 result={'formalArtifactAllowed':False,'accepted':all(x['passed'] for x in rows),'scope':'独立应用，正常库双播；其余故障为平台成功返回后的测试替换，不是真实GPU挂起','cases':rows};(R/'evidence/device-analysis.json').write_text(json.dumps(result,ensure_ascii=False,indent=2));print(json.dumps({x['scenario']:[k for k,v in x['checks'].items() if not v] for x in rows},ensure_ascii=False));return 0 if result['accepted'] else 1
if __name__=='__main__':raise SystemExit(main())
