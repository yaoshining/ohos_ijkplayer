import re,json,sys
from pathlib import Path

def parse(text):
 result=[]
 for line in text.splitlines():
  m=re.search(r'\b(P30_[A-Z]+)\s+(.*)',line)
  if m:
   row=dict(re.findall(r'(\w+)=([^\s]+)',m[2]));row['kind']=m[1];result.append(row)
 return result

def analyze(native,app,pid):
 failures=[]
 def need(ok,why):
  if not ok:failures.append(why)
 def one(rows,kind,op=None,**fields):
  found=[r for r in rows if r['kind']==kind and (op is None or r.get('op')==op) and all(r.get(k)==str(v)for k,v in fields.items())]
  if len(found)!=1:raise ValueError('missing/duplicate '+str((kind,op,fields)))
  return found[0]
 try:
  n=parse(native);a=parse(app);need(bool(n)and bool(a),'missing-events');need(not any(r.get('op')=='failed' for r in a),'application-failed')
  for rows in [n,a]:
   need(all(r.get('pid')==str(pid)for r in rows),'pid-mismatch')
   for kindgroup in [('P30_APP',),('P30_CODEC',),('P30_OWNER','P30_FRAME','P30_DRAIN')]:
    selected=[r for r in rows if r['kind']in kindgroup];seq=[int(r['seq'])for r in selected];t=[int(r['t'])for r in selected]
    need(len(seq)==len(set(seq))and seq==sorted(seq),'event-sequence');need(t==sorted(t),'event-time')
    need(all(int(r['tid'])>0 and int(r['t'])>0 for r in selected),'invalid-thread-or-time')
  ident=one(n,'P30_ID');owner=one(n,'P30_OWNER','create');consumer=ident['consumer'];need(int(consumer)>0 and ident['window_consumer']==consumer and ident['image_rc']==ident['window_rc']=='0','consumer-id')
  need(int(owner['owner'])>0 and owner.get('rc')=='0','owner-create-invalid')
  need(int(ident['image'],16)>0 and int(ident['window'],16)>0 and ident['owner']==owner['owner'],'owner-image')
  need(all(r.get('consumer')==consumer for r in n if r['kind']in ('P30_CODEC','P30_DRAIN','P30_FRAME')),'consumer-changed')
  need(all(r.get('owner')==owner['owner']for r in n if r['kind']in ('P30_DRAIN','P30_FRAME')),'owner-changed')
  visible=one(a,'P30_APP','api-visible');need(all(visible.get(k)=='1'for k in ['codec','mpv','arm','snapshot','release','waiting']),'api-not-visible')
  wait=one(n,'P30_CODEC','close-active-wait');old=wait['decoder'];confirmed=one(a,'P30_APP','close-wait-confirmed');need(confirmed['decoder']==old and confirmed['close_tid']==wait['tid'] and int(wait['rc'])>0,'not-actual-close-wait')
  need(int(wait['epoch'])==int(confirmed['epoch'])+1,'epoch-binding')
  requests=[one(a,'P30_APP','request-enter',request=q)for q in ['load','seek']];returned=[one(a,'P30_APP','request-return',request=q)for q in ['load','seek']]
  need(len({r['tid']for r in requests}|{confirmed['callback_tid'],confirmed['close_tid']})==4,'threads-not-distinct')
  blocked=one(a,'P30_APP','two-dispatch-waits');need({blocked['request_a_tid'],blocked['request_b_tid']}=={r['tid']for r in requests},'not-actual-dispatch-wait')
  release=one(a,'P30_APP','callback-release');drained=one(n,'P30_CODEC','close-active-drained',decoder=old);stop=one(n,'P30_CODEC','stop-end',decoder=old);destroy=one(n,'P30_CODEC','destroy-end',decoder=old)
  t=lambda r:int(r['t'])
  need(t(wait)<=t(confirmed)<min(t(r)for r in requests)<=max(t(r)for r in requests)<t(blocked)<t(release)<t(drained)<=t(stop)<=t(destroy),'close-request-release-order')
  for begin,end in zip(requests,returned):need(begin['tid']==end['tid']and t(end)>t(destroy),'request-return-order')
  need(returned[0]['rc']=='0'and returned[1]['rc']in ('0','-12'),'unexpected-command-return')
  joined=one(a,'P30_APP','joined');need(joined['callback_state']=='6'and t(joined)>max(t(r)for r in returned),'join-before-return')
  decs=[r for r in n if r['kind']=='P30_CODEC'and r.get('op')=='surface-begin'];need(len(decs)>=2 and len({r['decoder']for r in decs})==len(decs),'decoder-instances')
  previous_end=None
  for d in decs:
   dec=d['decoder'];need(int(dec)>0,'decoder-not-positive');surface=one(n,'P30_CODEC','surface-end',decoder=dec);start=one(n,'P30_CODEC','start-end',decoder=dec);end=one(n,'P30_CODEC','destroy-end',decoder=dec);stopd=one(n,'P30_CODEC','stop-end',decoder=dec)
   need(all(r['rc']=='0'for r in [d,surface,start,stopd,end]),'platform-error')
   need(t(d)<=t(surface)<=t(start)<t(stopd)<=t(end),'decoder-order')
   need(any(r['kind']=='P30_FRAME'and r.get('image')==ident['image']and t(start)<t(r)<t(stopd)for r in n),'missing-successful-map')
   need(any(r['kind']=='P30_DRAIN'and r.get('reason')=='2'and r.get('result')=='1'and r.get('platform')=='0'and t(start)<t(r)<t(stopd)for r in n),'missing-close-drain')
   if previous_end is not None:need(t(d)>t(previous_end),'new-producer-before-previous-destroy')
   previous_end=end
  ownerend=one(n,'P30_OWNER','destroy');need(ownerend['owner']==owner['owner'] and ownerend['consumer']==consumer,'owner-destroy-identity');need(t(ownerend)>max(t(r)for r in n if r['kind']=='P30_CODEC'),'early-owner-destroy')
  return {'accepted':not failures,'failures':failures,'pid':pid,'consumer':consumer,'decoderInstances':[d['decoder']for d in decs],'seekResult':int(returned[1]['rc']),'scope':'single-mpv-instance-controlled-real-thread-interleaving'}
 except (KeyError,ValueError,TypeError)as e:return {'accepted':False,'failures':failures+['malformed-or-missing:'+str(e)]}
if __name__=='__main__':
 r=analyze(Path(sys.argv[1]).read_text(),Path(sys.argv[2]).read_text(),int(sys.argv[3]));print(json.dumps(r,indent=2));sys.exit(not r['accepted'])
