"""离线结构完整性与区间分析；不推断旧事件，不等同3600秒验收。"""
import json,re
from pathlib import Path

def read_lanes(paths):
    rows,errors=[],[]
    for p in paths:
        for i,line in enumerate(p.read_bytes().splitlines(keepends=True)):
            try:
                if not line.endswith(b'\n'): raise ValueError('partial')
                rows.append(json.loads(line))
            except (ValueError,UnicodeError):errors.append('malformed_or_partial_line')
    return rows,errors

def analyze(rows,errors=(),heartbeat_gap_ns=15000000000):
    problems=list(errors)
    names=set('session_begin session_end sample_begin sample_end query_begin query_end heartbeat overdue ability_create ability_foreground ability_background ability_destroy stage_create stage_shown stage_resumed stage_paused stage_hidden stage_destroy window_active window_inactive surface_create surface_destroy late_event subscription_failed operator_action logging_error fault_delay run_begin run_end keep_awake_request keep_awake_success keep_awake_readback keep_awake_failure'.split())
    numeric='schema seq lane key generation monoNs wallNs durationNs rc'.split()
    valid=[]
    for r in rows:
        if not isinstance(r,dict) or any(type(r.get(k)) is not int for k in numeric) or r.get('schema')!=1 or r.get('lane') not in (0,1,2) or r.get('event') not in names or not isinstance(r.get('session'),str) or not re.fullmatch('[a-f0-9]+-[a-f0-9]+-[a-f0-9]+',r['session']):
            problems.append('invalid_schema');continue
        if min(r['key'],r['generation'],r['monoNs'],r['durationNs'])<0 or r['seq']<1:problems.append('invalid_numeric_domain')
        if 'callStartNs' in r and (type(r['callStartNs']) is not int or r['callStartNs']<0):problems.append('invalid_actual_call_interval')
        expected_lane=2 if r['event'] in ('heartbeat','overdue') else 1 if r['event'].startswith(('query_','sample_','run_')) or r['event']=='fault_delay' else 0
        if r['lane']!=expected_lane:problems.append('invalid_lane')
        valid.append(r)
    rows=sorted(valid,key=lambda x:x['seq'])
    if not rows:return dict(complete=False,continuousEligible=False,coverageComplete=False,problems=sorted(set(problems+['empty'])))
    seq=[r.get('seq') for r in rows]
    if seq!=list(range(1,len(seq)+1)):problems.append('missing_or_duplicate_sequence')
    if len({r.get('session') for r in rows})!=1:problems.append('mixed_session')
    if rows[0].get('event')!='session_begin' or rows[-1].get('event')!='session_end':problems.append('session_not_closed')
    if sum(r['event']=='session_begin' for r in rows)!=1 or sum(r['event']=='session_end' for r in rows)!=1:problems.append('session_boundary_count')
    run_count=0;paired_samples=0
    queries={};samples={};runs={};active_run=None;run_bindings={};paired=0;durations=[];background=False;heartbeats=[];overdues=[];fault=False;wall_change=False;last={}
    for r in rows:
        try:
            e=r['event'];lane=r['lane'];m=r['monoNs'];w=r['wallNs'];s=r['seq'];k=r['key']
            previous=last.get(lane)
            if previous:
                if m<previous[0]:problems.append('monotonic_regression')
                if abs((w-previous[1])-(m-previous[0]))>1000000000:wall_change=True
            last[lane]=(m,w)
            if e=='run_begin':
                run_count+=1
                if active_run is not None:problems.append('overlapping_run')
                runs[s]=r;active_run=s
            if e=='run_end':
                start=runs.pop(k,None)
                if start is None or active_run!=k or start['generation']!=r['generation']:problems.append('unpaired_run')
                if queries or samples:problems.append('run_ended_with_open_intervals')
                active_run=None
            if e=='query_begin':
                queries[s]=r;run_bindings[s]=active_run
                if active_run is None:problems.append('query_outside_run')
            if e=='sample_begin':
                samples[s]=r;run_bindings[s]=active_run
                if active_run is None or k!=active_run:problems.append('sample_outside_run')
            if e in ('query_end','sample_end'):
                opens=queries if e=='query_end' else samples
                start=opens.pop(k,None)
                if start is None or m<start['monoNs'] or r['durationNs']<0 or r['generation']!=start['generation'] or run_bindings.get(k)!=active_run:problems.append('unpaired_or_invalid_end')
                elif e=='sample_end':paired_samples+=1
                elif e=='query_end':
                    paired+=1;durations.append(r['durationNs'])
                    call_start=r.get('callStartNs',0)
                    if type(call_start) is int and call_start and (call_start<start['monoNs'] or call_start+r['durationNs']>m):problems.append('invalid_actual_call_interval')
            if e=='ability_background':background=True
            if e=='heartbeat':heartbeats.append(m)
            if e=='overdue':overdues.append(k)
            if e=='fault_delay':fault=True
            if e in ('subscription_failed','logging_error','keep_awake_failure') or (e=='session_end' and r['rc']!=0):problems.append('recording_error')
        except (KeyError,TypeError,ValueError):problems.append('invalid_record')
    if queries or samples or runs:problems.append('open_interval')
    if len(heartbeats)<2:problems.append('insufficient_heartbeat')
    coverage_gaps=[]
    if heartbeats:
        points=[rows[0]['monoNs']]+heartbeats+[rows[-1]['monoNs']]
        coverage_gaps=[(a,b) for a,b in zip(points,points[1:]) if b-a>heartbeat_gap_ns]
    coverage_complete=len(heartbeats)>=2 and not coverage_gaps
    complete=not problems
    return dict(complete=complete,problems=sorted(set(problems)),records=len(rows),session=rows[0].get('session'),pairedQueries=paired,maxQueryMs=max(durations,default=0)/1e6,openQueries=list(queries),openSamples=list(samples),heartbeatCount=len(heartbeats),maxHeartbeatGapMs=max((b-a for a,b in zip(heartbeats,heartbeats[1:])),default=0)/1e6,overdueQueries=sorted(set(overdues)),backgroundObserved=background,faultInjected=fault,wallClockAdjustment=wall_change,coverageComplete=coverage_complete,heartbeatGapLimitMs=heartbeat_gap_ns/1e6,heartbeatCoverageGaps=coverage_gaps,pairedSamples=paired_samples,runCount=run_count,continuousEligible=complete and coverage_complete and paired_samples>0 and paired>0 and run_count==1 and not background and not fault,oldGapRootCauseResolved=False)
if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('directory');p.add_argument('--output');args=p.parse_args()
    rows,errors=read_lanes(sorted(Path(args.directory).glob('timeline-*.jsonl')));r=analyze(rows,errors);s=json.dumps(r,ensure_ascii=False,indent=2)+'\n'
    if args.output:Path(args.output).write_text(s)
    print(s)
