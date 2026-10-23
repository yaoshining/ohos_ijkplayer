"""只接受同一进程/owner/consumer 的三代 decoder 真实帧和两次关闭交接。"""
import re,json,sys
from pathlib import Path
def _analyze(text,pid):
 events=[]
 for line in text.splitlines():
  m=re.search(r'\b(P30_(?:OWNER|ID|CODEC|DRAIN|FRAME))\s+(.*)',line)
  if m:
   e=dict(re.findall(r'(\w+)=([^\s]+)',m[2]));e['kind']=m[1];events.append(e)
 failures=[]
 def require(b,msg):
  if not b: failures.append(msg)
 require(bool(events),'missing-trace')
 require(all(e.get('t','').isdigit() and int(e['t'])>0 for e in events if e['kind']!='P30_ID'),'invalid-time')
 if failures:return {'accepted':False,'failures':failures,'handoffs':0}
 require(all(e.get('tid','').isdigit() and int(e['tid'])>0 for e in events if e['kind']!='P30_ID'),'missing-or-invalid-tid')
 for group in [('P30_CODEC',),('P30_OWNER','P30_DRAIN','P30_FRAME')]:
  seq=[e.get('seq') for e in events if e['kind'] in group]
  require(all(x and x.isdigit() and int(x)>0 for x in seq) and len(seq)==len(set(seq)),'duplicate-or-invalid-event-seq')
  require([int(x) for x in seq]==sorted(int(x) for x in seq),'out-of-order-event-seq')
  times=[int(e['t']) for e in events if e['kind'] in group]
  require(times==sorted(times),'out-of-order-time')
 require(all(e.get('pid')==str(pid) for e in events),'wrong-or-missing-pid')
 owners=[e for e in events if e['kind']=='P30_OWNER' and e.get('op')=='create']; ids=[e for e in events if e['kind']=='P30_ID']
 require(len(owners)==1 and len(ids)==1,'owner-recreated-or-missing')
 if len(owners)!=1 or len(ids)!=1:return {'accepted':False,'failures':failures,'handoffs':0}
 owner=owners[0]['owner']; ident=ids[0]; consumer=ident.get('consumer')
 for field in ['image','window']:
  require(bool(re.fullmatch(r'0x[0-9a-fA-F]+',ident.get(field,''))) and int(ident.get(field,'0'),16)>0,'missing-or-zero-'+field)
 require(owner.isdigit() and int(owner)>0,'invalid-owner')
 require(consumer not in ('0',None) and ident.get('window_consumer')==consumer and ident.get('image_rc')=='0' and ident.get('window_rc')=='0','consumer-query-invalid')
 require(ident.get('owner')==owner and owners[0].get('rc')=='0','owner-identity-invalid')
 require(all(e.get('consumer')==consumer for e in events if e['kind'] in ('P30_CODEC','P30_DRAIN','P30_FRAME')),'consumer-changed')
 require(all(e.get('owner')==owner for e in events if e['kind'] in ('P30_DRAIN','P30_FRAME')),'owner-changed')
 decs=[]
 for e in events:
  if e['kind']=='P30_CODEC' and e.get('op')=='surface-begin':decs.append(e['decoder'])
 require(all(d.isdigit() and int(d)>0 for d in decs),'invalid-decoder-instance')
 require(len(decs)>=3 and len(set(decs))==len(decs),'need-three-unique-decoders')
 records=[]
 for dec in decs:
  row={}
  for op in ['surface-begin','surface-end','start-end','stop-end','destroy-end']:
   matches=[e for e in events if e['kind']=='P30_CODEC' and e.get('decoder')==dec and e.get('op')==op]
   require(len(matches)==1,'decoder-'+dec+'-'+op+'-missing-or-duplicate')
   if len(matches)==1:
    row[op]=int(matches[0]['t']);require(matches[0].get('rc')=='0','platform-error-'+op)
  if len(row)!=5:continue
  require(row['surface-begin']<=row['surface-end']<=row['start-end']<row['stop-end']<=row['destroy-end'],'decoder-order')
  frames=[e for e in events if e['kind']=='P30_FRAME' and row['start-end']<=int(e['t'])<row['stop-end'] and e.get('image')==ident.get('image')]
  require(bool(frames),'decoder-'+dec+'-no-actual-frame')
  drains=[e for e in events if e['kind']=='P30_DRAIN' and e.get('reason')=='2' and e.get('result')=='1' and e.get('platform')=='0' and row['start-end']<int(e['t'])<row['stop-end']]
  require(bool(drains),'decoder-'+dec+'-no-close-drain')
  records.append(row)
 destroyed=[e for e in events if e['kind']=='P30_OWNER' and e.get('op')=='destroy']
 require(len(destroyed)==1 and destroyed[0].get('owner')==owner and int(destroyed[0]['t'])>max((int(e['t']) for e in events if e['kind'] in ('P30_FRAME','P30_CODEC')),default=0),'early-or-missing-owner-destroy')
 for a,b in zip(records,records[1:]):require(a['destroy-end']<b['surface-begin'],'early-new-producer')
 return {'accepted':not failures,'failures':failures,'handoffs':max(0,len(records)-1),'pid':pid,'owner':owner,'consumer':consumer}
def analyze(text,pid):
 try:return _analyze(text,pid)
 except (KeyError,ValueError,TypeError) as e:return {'accepted':False,'failures':['malformed-event:'+str(e)],'handoffs':0}
if __name__=='__main__':
 r=analyze(Path(sys.argv[1]).read_text(),int(sys.argv[2]));print(json.dumps(r,indent=2));sys.exit(not r['accepted'])
