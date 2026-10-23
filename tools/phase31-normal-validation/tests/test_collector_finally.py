import sys,unittest,tempfile,contextlib,io
from pathlib import Path
from unittest.mock import patch
from types import SimpleNamespace
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'device'));import run
class Flow(unittest.TestCase):
 def replay(self,fault,keep=False):
  calls=[];state={'started':False,'stopped':False,'ls':0}
  def execute(cmd,**kwargs):
   tail=cmd[3:];calls.append(tail);rc=0;out=''
   if tail[:2]==['list','targets']:out=run.T+' TCP Connected\n'
   elif tail[:3]==['shell','aa','force-stop']:state['stopped']=True;out='force stop process successfully'
   elif tail[:3]==['shell','aa','start']:
    state.update(started=True,stopped=False)
    if fault=='start-timeout':raise run.subprocess.TimeoutExpired(cmd,15)
    out='start ability successfully'
   elif tail[:2]==['shell','pidof']:out='1234\n' if state['started'] and not state['stopped'] else ''
   elif tail[:2]==['shell','ls']:
    state['ls']+=1
    if fault=='ls' and state['ls']==3:rc=1;out='error: failed'
    else:out='vk-pq-0.log\nvk-pq-result.txt\n'
   elif tail[:2]==['shell','cat']:
    out='loaded=1 eof=1 errors=0' if tail[2].endswith('result.txt') else 'P24_BEGIN case=vk-pq pid=1234\nP24_RESULT loaded=1 eof=1 errors=0\n'
   elif tail[:2]==['shell','tail']:out='P24_OBSERVATION {}'
   elif tail[:3]==['shell','aa','dump']:out='AbilityManagerService current mission lists'
   elif tail[:2]==['shell','hidumper']:out='WindowManagerService Total window num 0'
   elif tail[:2]==['file','recv']:
    if fault=='recv':rc=1;out='error: transfer failed'
    else:Path(tail[-1]).write_text('fixture');out='FileTransfer finish'
   return SimpleNamespace(returncode=rc,stdout=out,stderr='')
  with tempfile.TemporaryDirectory() as d:
   args=['run','--mode','vk-pq','--out',d+'/result']+(['--keep-process'] if keep else [])
   with patch.object(sys,'argv',args),patch.object(run.subprocess,'run',execute),patch.object(run.time,'sleep',lambda _:None),contextlib.redirect_stdout(io.StringIO()):
    try:run.main()
    except (RuntimeError,SystemExit):pass
   starts=[i for i,c in enumerate(calls) if c[:3]==['shell','aa','start']];stops=[i for i,c in enumerate(calls) if c[:3]==['shell','aa','force-stop']]
   self.assertTrue(starts);self.assertTrue(any(i>starts[-1] for i in stops),'cleanup missing after '+fault)
   self.assertTrue((Path(d)/'result/cleanup.json').is_file(),'cleanup evidence missing')
 def test_start_timeout(self):self.replay('start-timeout')
 def test_recv_failure(self):self.replay('recv')
 def test_ls_failure(self):self.replay('ls')
 def test_keep_process_failure(self):self.replay('recv',True)
if __name__=='__main__':unittest.main()
