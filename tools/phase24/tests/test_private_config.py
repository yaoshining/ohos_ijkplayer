import pathlib,sys,unittest,tempfile,json,struct
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/'tools'))
from private_config import canonical_smb,make_device_config
class PrivateConfigTests(unittest.TestCase):
 def test_chinese_encoding_once(self):
  raw='smb://192.0.2.1/Share/中文/电影 4K.mp4'
  encoded=canonical_smb(raw)
  self.assertIn('%E4%B8%AD',encoded);self.assertNotIn('中文',encoded)
  self.assertEqual(canonical_smb(encoded),encoded)
 def test_reject_userinfo(self):
  for url in ['smb://u:secret@host/share/x','file:///tmp/x','smb://host/share/x\n']:
   with self.assertRaisesRegex(ValueError,'invalid SMB location'):canonical_smb(url)
 def test_private_binary_not_url_credentials(self):
  b=make_device_config('smb://host/share/中文.mp4',{'username':'user','password':'a,:@% =','domain':'D'})
  n=struct.unpack_from('<I',b)[0];url=b[4:4+n].decode()
  self.assertNotIn('@',url);self.assertNotIn('a,:',url)
  self.assertIn(b'a,:@% =',b)
