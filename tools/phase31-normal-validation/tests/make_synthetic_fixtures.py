"""合成 UI 生命周期夹具，无设备日志、私人媒体或实际 PID/会话。"""
import json
from pathlib import Path
ROOT=Path(__file__).parent/'fixtures';ROOT.mkdir(exist_ok=True)
def timeline(background):
 rows=[];session='abc-def-123'
 def event(t,name,key=0,g=0,rc=0,lane=0,ident=None):
  r=dict(schema=1,session=session,seq=0,lane=lane,event=name,key=key,generation=g,monoNs=int((100+t)*1e9),wallNs=int((1000+t)*1e9),durationNs=0,rc=rc,callStartNs=0)
  rows.append((t,r,ident));return ident
 event(0,'session_begin',rc=1001);event(.01,'ability_create');event(.02,'stage_create',g=1);event(.03,'ability_foreground');event(.04,'stage_shown',g=1);event(.05,'window_active',g=1);event(.06,'surface_create',g=1);event(.07,'keep_awake_readback',key=1,g=1)
 event(.1,'run_begin',lane=1,ident='run')
 end=32 if background else 5
 for i in range(end):event(i+.5,'heartbeat',lane=2)
 obs=[]
 if background:
  event(9.99,'window_inactive',g=1);event(10,'ability_background');event(10.01,'stage_hidden',g=1);event(15,'ability_foreground');event(15.01,'stage_shown',g=1);event(15.02,'window_active',g=1)
  for i in range(1,31):
   event(i,'sample_begin',key='run',lane=1,ident='sample'+str(i));event(i+.01,'sample_end',key='sample'+str(i),lane=1)
   obs.append(dict(t=i,fileIndex=0,videoSampleRc=0,**{'time-pos':dict(rc=0,value=i)}))
  event(31,'run_end',key='run',lane=1)
 else:
  event(1,'query_begin',g=103,lane=1,ident='destroy');event(2,'query_end',key='destroy',g=103,lane=1);event(2.5,'run_end',key='run',lane=1)
 event(end-.2,'keep_awake_readback',key=0,g=1);event(end,'session_end')
 rows.sort(key=lambda x:x[0]);ids={ident:i+1 for i,(_,_,ident) in enumerate(rows) if ident}
 for i,(_,r,_) in enumerate(rows):
  r['seq']=i+1
  if isinstance(r['key'],str):r['key']=ids[r['key']]
 return [r for _,r,_ in rows],obs
rows,obs=timeline(True);(ROOT/'background.json').write_text(json.dumps({'rows':rows,'text':'P24_BEGIN case=vk-background pid=1001\nP24_FILE_LOADED index=0\n'+'\n'.join('P24_OBSERVATION '+json.dumps(r) for r in obs)},indent=2))
rows,_=timeline(False);cmd=lambda out:dict(exit=0,stdout=out,stderr='')
(ROOT/'close.json').write_text(json.dumps({'rows':rows,'marker':dict(requested=True,cleanBeforeClose=True,afterSessionEnd=True),'before':{'pid':cmd(''),'ability':cmd('AbilityManagerService current mission lists'),'window':cmd('WindowManagerService Total window num 0'),'targets':cmd('192.168.3.85:5555 TCP Connected')}},indent=2))
