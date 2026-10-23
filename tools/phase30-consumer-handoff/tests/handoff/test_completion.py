import sys,json
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'device'))
from completion_gate import completed
mode='vk-concurrent-switch';result='loaded=2 eof=1 errors=0';log='P24_BEGIN case='+mode+' pid=1\nP24_RESULT '+result
cases=[('good',{'exit':0,'stdout':result},log,True),('missing-result',{'exit':1,'stdout':'cat: No such file'},'',False),('empty-plan',{'exit':0,'stdout':result},'',False),('wrong-mode',{'exit':0,'stdout':result},log.replace(mode,'vk-pq'),False),('timeout',{'exit':0,'stdout':result,'timeout':15},log,False)]
rows=[{'name':n,'passed':completed(mode,c,l)==e}for n,c,l,e in cases];print(json.dumps({'cases':rows,'accepted':all(x['passed']for x in rows)},indent=2));sys.exit(not all(x['passed']for x in rows))
