"""合成命令记录测试：不连接目标、不重放真实私人设备日志。"""
import copy,json,sys
from pathlib import Path
from cleanup_gate import derive_cleanup,TARGET,BUNDLE

def command(args,stdout='',exit=0):return {'command':args,'stdout':stdout,'stderr':'','exit':exit}
def positive():return [command(['shell','aa','start','-b',BUNDLE]),command(['shell','aa','force-stop',BUNDLE],'force stop process successfully'),command(['shell','pidof',BUNDLE]),command(['shell','hidumper','-s','WindowManagerService'],'WindowManagerService\nTotal window num: 0'),command(['shell','aa','dump','-a'],'AbilityManagerService\ncurrent mission lists: 0'),command(['list','targets','-v'],TARGET+' TCP Connected')]
def accepted(c):
 x,_=derive_cleanup(c)
 return x['cleanupEvidenceValid'] and x['pidAbsent'] and x['windowAbsent'] and x['abilityAbsent'] and not x['targetOffline']
def main():
 rows=[]
 def case(name,c,want):rows.append({'case':name,'expected':want,'actual':accepted(c),'passed':accepted(c)==want})
 case('valid-empty-pid',positive(),True)
 c=positive();c[2]['exit']=1;case('valid-pid-exit-one',c,True)
 c=positive();c[2]['timeout']=3;case('pid-timeout',c,False)
 c=positive();c[-1]['stdout']=TARGET+' TCP Offline';case('offline',c,False)
 c=positive();c[1]['stdout']='failed';case('stop-semantic-failure',c,False)
 c=positive();c.pop(4);case('missing-ability',c,False)
 case('stop-only',positive()[:2],False)
 c=positive()
 for x in c[2:]:x.update(stdout='',timeout=3)
 case('timeout-empty',c,False)
 c=positive();c[3]['stdout']+='\nphase22probe';case('window-present',c,False)
 c=positive();c[4]['stdout']+='\n'+BUNDLE;case('ability-present',c,False)
 c=positive();c[2]['stderr']='error: transport failed';case('pid-error',c,False)
 result={'syntheticOnly':True,'deviceExecuted':False,'cases':rows,'accepted':all(x['passed'] for x in rows)}
 print(json.dumps(result,indent=2));sys.exit(0 if result['accepted'] else 1)
if __name__=='__main__':main()
