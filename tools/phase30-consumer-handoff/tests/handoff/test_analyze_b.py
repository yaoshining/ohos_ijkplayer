from pathlib import Path
import json,sys
from analyze_b import analyze
N='''P30_OWNER seq=1 t=1 pid=9 tid=10 op=create owner=1 generation=1 consumer=88 rc=0
P30_ID pid=9 owner=1 image=0xabc window=0xdef consumer=88 window_consumer=88 image_rc=0 window_rc=0
P30_CODEC seq=1 t=2 pid=9 tid=20 op=surface-begin decoder=1 consumer=88 epoch=0 rc=0
P30_CODEC seq=2 t=3 pid=9 tid=20 op=surface-end decoder=1 consumer=88 epoch=0 rc=0
P30_CODEC seq=3 t=4 pid=9 tid=20 op=start-end decoder=1 consumer=88 epoch=0 rc=0
P30_FRAME seq=2 t=5 pid=9 tid=10 owner=1 consumer=88 image=0xabc pts=0.1
P30_DRAIN seq=3 t=10 pid=9 tid=10 owner=1 consumer=88 reason=2 result=1 platform=0
P30_CODEC seq=4 t=11 pid=9 tid=20 op=close-active-wait decoder=1 consumer=88 epoch=2 rc=1
P30_CODEC seq=5 t=20 pid=9 tid=20 op=close-active-drained decoder=1 consumer=88 epoch=2 rc=0
P30_CODEC seq=6 t=21 pid=9 tid=20 op=stop-end decoder=1 consumer=88 epoch=2 rc=0
P30_CODEC seq=7 t=22 pid=9 tid=20 op=destroy-end decoder=1 consumer=88 epoch=2 rc=0
P30_CODEC seq=8 t=26 pid=9 tid=20 op=surface-begin decoder=2 consumer=88 epoch=0 rc=0
P30_CODEC seq=9 t=27 pid=9 tid=20 op=surface-end decoder=2 consumer=88 epoch=0 rc=0
P30_CODEC seq=10 t=28 pid=9 tid=20 op=start-end decoder=2 consumer=88 epoch=0 rc=0
P30_FRAME seq=4 t=29 pid=9 tid=10 owner=1 consumer=88 image=0xabc pts=0.1
P30_DRAIN seq=5 t=30 pid=9 tid=10 owner=1 consumer=88 reason=2 result=1 platform=0
P30_CODEC seq=11 t=31 pid=9 tid=20 op=stop-end decoder=2 consumer=88 epoch=2 rc=0
P30_CODEC seq=12 t=32 pid=9 tid=20 op=destroy-end decoder=2 consumer=88 epoch=2 rc=0
P30_OWNER seq=6 t=33 pid=9 tid=10 op=destroy owner=1 generation=1 consumer=88 rc=0
'''
A='''P30_APP seq=1 t=8 pid=9 tid=30 op=api-visible codec=1 mpv=1 arm=1 snapshot=1 release=1 waiting=1
P30_APP seq=2 t=9 pid=9 tid=30 op=armed decoder=1
P30_APP seq=3 t=12 pid=9 tid=30 op=close-wait-confirmed decoder=1 epoch=1 callback_tid=40 close_tid=20
P30_APP seq=4 t=13 pid=9 tid=50 op=request-enter request=load
P30_APP seq=5 t=14 pid=9 tid=51 op=request-enter request=seek
P30_APP seq=6 t=15 pid=9 tid=30 op=two-dispatch-waits request_a_tid=50 request_b_tid=51
P30_APP seq=7 t=16 pid=9 tid=30 op=callback-release
P30_APP seq=8 t=23 pid=9 tid=50 op=request-return request=load rc=0
P30_APP seq=9 t=24 pid=9 tid=51 op=request-return request=seek rc=-12
P30_APP seq=10 t=25 pid=9 tid=30 op=joined callback_state=6
'''
cases=[('good',N,A,True),('early-release',N,A.replace('t=16','t=14'),False),('not-real-dispatch-wait',N,A.replace('op=two-dispatch-waits','op=application-before-call'),False),('same-tid',N,A.replace('tid=51','tid=50'),False),('wrong-pid',N,A.replace('pid=9','pid=8',1),False),('early-new-surface',N.replace('t=26','t=19'),A,False),('missing-request-return',N,'\n'.join(x for x in A.splitlines()if' request=seek rc='not in x),False),('flush-only',N.replace('op=close-active-wait','op=flush-active-wait'),A,False),('no-frame',N.replace('P30_FRAME','P30_ACQUIRE'),A,False)]
# Three valid generations, then overlap generation 2 and 3 without breaking per-module ordering.
third='P30_CODEC seq=13 t=34 pid=9 tid=20 op=surface-begin decoder=3 consumer=88 epoch=0 rc=0\nP30_CODEC seq=14 t=35 pid=9 tid=20 op=surface-end decoder=3 consumer=88 epoch=0 rc=0\nP30_CODEC seq=15 t=36 pid=9 tid=20 op=start-end decoder=3 consumer=88 epoch=0 rc=0\nP30_FRAME seq=6 t=37 pid=9 tid=10 owner=1 consumer=88 image=0xabc pts=0.1\nP30_DRAIN seq=7 t=38 pid=9 tid=10 owner=1 consumer=88 reason=2 result=1 platform=0\nP30_CODEC seq=16 t=39 pid=9 tid=20 op=stop-end decoder=3 consumer=88 epoch=2 rc=0\nP30_CODEC seq=17 t=40 pid=9 tid=20 op=destroy-end decoder=3 consumer=88 epoch=2 rc=0\nP30_OWNER seq=8 t=41 pid=9 tid=10 op=destroy owner=1 generation=1 consumer=88 rc=0\n'
N3=N[:N.index('P30_OWNER seq=6')]+third
# Reorder only codec seq to maintain a valid trace whose generation 3 binds before generation 2 destroys.
lines=N3.splitlines();old=[x for x in lines if 'op=destroy-end decoder=2' in x][0];lines.remove(old);pos=next(i for i,x in enumerate(lines)if 'op=start-end decoder=3' in x);lines.insert(pos+1,old.replace('t=32','t=36'))
import re
k=0
for i,line in enumerate(lines):
 if line.startswith('P30_CODEC'):
  k+=1;lines[i]=re.sub(r'seq=\d+',f'seq={k}',line)
overlap='\n'.join(lines)
cases += [('owner-create-error',N.replace('consumer=88 rc=0','consumer=88 rc=-1',1),A,False),('zero-owner',N.replace('owner=1','owner=0'),A,False),('zero-decoder',N.replace('decoder=1','decoder=0'),A.replace('decoder=1','decoder=0'),False),('owner-destroy-mismatch',N.replace('op=destroy owner=1','op=destroy owner=2'),A,False),('app-failed',N,A+'P30_APP seq=11 t=26 pid=9 tid=30 op=failed reason=test\n',False),('three-good',N3,A,True),('third-overlap',overlap,A,False)]
out=Path(sys.argv[1]);out.mkdir(parents=True,exist_ok=False);rows=[]
for n,native,app,want in cases:
 r=analyze(native,app,9);rows.append({'name':n,'expected':want,'actual':r,'passed':r['accepted']==want})
(out/'results.json').write_text(json.dumps({'syntheticParserFixtures':True,'cases':rows,'accepted':all(r['passed']for r in rows)},indent=2)+'\n');print([(r['name'],r['passed'])for r in rows]);sys.exit(not all(r['passed']for r in rows))
