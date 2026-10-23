import pathlib,sys,unittest,tempfile,json,types
from unittest.mock import patch
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/'tools'))
import nas_preflight
class PreflightTests(unittest.TestCase):
 def test_exact_readonly_file_and_partial_identity(self):
  calls=[]
  class Client:
   def __init__(self,*a,**k):pass
   def login(self,*a):calls.append(('login',))
   def connectTree(self,s):calls.append(('share',s));return 1
   def openFile(self,t,p,**k):calls.append(('open',p,k));return 2
   def queryInfo(self,t,f,fileInfoClass=None):return {'LastWriteTime':123} if fileInfoClass else {'EndOfFile':100000}
   def readFile(self,t,f,o,n):calls.append(('read',o,n));return b'x'*n
   def getDialect(self):return 0x311
   def closeFile(self,*a):calls.append(('close',))
   def logoff(self):pass
   def close(self):pass
  class Server:
   server_port=12345
   def __init__(self,*a):pass
   def serve_forever(self):pass
   def shutdown(self):pass
   def server_close(self):pass
  mods={'impacket':types.ModuleType('impacket'),'impacket.smbconnection':types.SimpleNamespace(SMBConnection=Client),'impacket.smb3structs':types.SimpleNamespace(FILE_READ_DATA=1,FILE_READ_ATTRIBUTES=128,FILE_OPEN=1,SMB2_FILE_BASIC_INFO=4,FILE_BASIC_INFORMATION=lambda b:b)}
  with tempfile.TemporaryDirectory() as d:
   p=pathlib.Path(d)/'auth';p.write_text(json.dumps({'username':'u','password':'secret'}));p.chmod(0o600)
   probe=types.SimpleNamespace(returncode=0,stdout=json.dumps({'format':{'duration':'8000','filename':'private','tags':{'title':'private'}},'streams':[{'codec_name':'hevc','codec_type':'video','tags':{'title':'private'}}]}).encode())
   with patch.dict(sys.modules,mods),patch('nas_preflight.subprocess.run',return_value=probe),patch('nas_preflight.http.server.ThreadingHTTPServer',Server):r=nas_preflight.run('smb://example/Share/目录/file.mp4',p)
   self.assertTrue(r['okay']);self.assertEqual(r['lastWriteTime'],123)
   self.assertFalse(r['fullFileHashVerified']);self.assertIsNone(r['fullFileSHA256']);self.assertEqual(r['prefixBytes'],65536)
   self.assertNotIn('secret',json.dumps(r));self.assertNotIn('private',json.dumps(r))
   self.assertIn(('open','目录\\file.mp4',{'desiredAccess':129,'creationDisposition':1}),calls)
   self.assertIn(('close',),calls)
