from analyze_a import analyze
from pathlib import Path
import json,sys
# 人造解析夹具仅测试证据门禁，不是设备执行证据。
lines=['P30_OWNER seq=1 t=1 pid=9 tid=10 op=create owner=1 generation=1 consumer=888 rc=0','P30_ID pid=9 owner=1 image=0xabc window=0xdef consumer=888 window_consumer=888 image_rc=0 window_rc=0']
seq=1
for d in range(1,4):
 t=d*100
 for op,offset in [('surface-begin',0),('surface-end',1),('start-end',2),('stop-end',80),('destroy-end',90)]:
  lines.append(f'P30_CODEC seq={seq} t={t+offset} pid=9 tid=20 op={op} decoder={d} consumer=888 epoch=0 rc=0');seq+=1
 lines.append(f'P30_FRAME seq={d*2} t={t+10} pid=9 tid=10 owner=1 consumer=888 image=0xabc map_index={d} pts=0.1')
 lines.append(f'P30_DRAIN seq={d*2+1} t={t+70} pid=9 tid=10 owner=1 consumer=888 reason=2 result=1 platform=0')
lines.append('P30_OWNER seq=8 t=500 pid=9 tid=10 op=destroy owner=1 generation=1 consumer=888 rc=0')
base='\n'.join(lines)
cases=[('positive',base,True),('wrong-pid',base.replace('pid=9','pid=99',1),False),('missing-id',base.replace('window_consumer=888','display_consumer=888'),False),('query-failure',base.replace('image_rc=0','image_rc=-1'),False),('consumer-changed',base.replace('decoder=3 consumer=888','decoder=3 consumer=889'),False),('no-close-drain',base.replace('reason=2','reason=1'),False),('no-frame','\n'.join(x for x in lines if 'P30_FRAME' not in x),False),('early-bind',base.replace('t=200','t=150'),False),('missing-tid',base.replace('tid=20','tid=0'),False),('duplicate-codec-seq',base.replace('seq=2 t=101','seq=1 t=101'),False)]
cases += [('missing-both-image',base.replace('image=0xabc ',''),False),('zero-window',base.replace('window=0xdef','window=0x0'),False),('zero-decoder',base.replace('decoder=1','decoder=0'),False),('missing-time',base.replace('t=101 ',''),False),('early-owner-destroy',base.replace('seq=8 t=500','seq=8 t=50'),False),('sequence-reversed',base.replace('seq=3 t=102','seq=99 t=102'),False)]
out=Path(sys.argv[1]);out.mkdir(parents=True,exist_ok=False);rows=[]
for name,data,expected in cases:
 try: result=analyze(data,9)
 except Exception as e: result={'accepted':None,'uncaught':repr(e)}
 rows.append({'name':name,'expected':expected,'actual':result,'passed':result['accepted']==expected})
(out/'results.json').write_text(json.dumps({'fixtureOnly':True,'cases':rows,'accepted':all(r['passed'] for r in rows)},indent=2)+'\n');print([(r['name'],r['passed'])for r in rows]);sys.exit(not all(r['passed'] for r in rows))
