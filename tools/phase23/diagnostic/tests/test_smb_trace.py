import importlib.util
from pathlib import Path
import unittest
p=Path(__file__).resolve().parents[1]/'smb_trace.py'
spec=importlib.util.spec_from_file_location('smb_trace',p);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
class Core:
 def __init__(self, handler): self.handlers={('smb1',114):handler,('smb2',1):handler}
 def hookSmbCommand(self,n,f):old=self.handlers['smb1',n];self.handlers['smb1',n]=f;return old
 def hookSmb2Command(self,n,f):old=self.handlers['smb2',n];self.handlers['smb2',n]=f;return old
class Trace(unittest.TestCase):
 def test_preserves_handler_identity_and_redacts_packet(self):
  called=[];result=([object()],None,0xc000006d)
  def handler(*args):called.append(args);return result
  core=Core(handler);events=[];module.install(core,[('smb1',114),('smb2',1)],lambda event,**kw:events.append((event,kw)))
  packet={'password':'must-never-log-secret','Data':'NTLM-private-material'}
  for key in [('smb1',114),('smb2',1)]:self.assertIs(core.handlers[key]('conn',core,packet),result)
  self.assertEqual(len(called),2);self.assertEqual(len(events),4)
  self.assertEqual(events[1][1]['status'],0xc000006d)
  self.assertNotIn('must-never-log-secret',repr(events));self.assertNotIn('NTLM-private-material',repr(events))
 def test_negotiate_preserves_smb1_transition_argument(self):
  called=[]
  def handler(*args,**kwargs):called.append((args,kwargs));return ([],None,0)
  core=Core(handler);module.install(core,[('smb2',1)],lambda *a,**kw:None)
  core.handlers['smb2',1]('conn',core,{},True)
  self.assertEqual(called[0][0][-1],True)
  core.handlers['smb2',1]('conn',core,{},isSMB1=True)
  self.assertEqual(called[1][1],{'isSMB1':True})
 def test_preserves_exception_and_only_emits_type(self):
  error=ValueError('secret material')
  def handler(*a):raise error
  core=Core(handler);events=[];module.install(core,[('smb2',1)],lambda event,**kw:events.append((event,kw)))
  with self.assertRaises(ValueError) as caught:core.handlers['smb2',1]('conn',core,{})
  self.assertIs(caught.exception,error);self.assertEqual(events[-1][1]['exception'],'ValueError');self.assertNotIn('secret material',repr(events))
if __name__=='__main__':unittest.main()
