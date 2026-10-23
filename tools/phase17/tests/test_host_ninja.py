from pathlib import Path
import unittest,sys,io,zipfile,hashlib,struct
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from host_ninja import verified_binary
class HostNinjaTests(unittest.TestCase):
 def package(self,machine=62,extra=False):
  data=b'\x7fELF\x02\x01\x01'+b'\0'*11+struct.pack('<H',machine)+b'payload';f=io.BytesIO()
  with zipfile.ZipFile(f,'w')as z:
   z.writestr('ninja',data)
   if extra:z.writestr('../other',b'not allowed')
  raw=f.getvalue();return raw,{'archiveSHA256':hashlib.sha256(raw).hexdigest(),'binarySHA256':hashlib.sha256(data).hexdigest()},data
 def test_pinned_x86_64_binary(self):
  raw,lock,data=self.package();self.assertEqual(verified_binary(raw,lock),data)
 def test_changed_archive_rejected(self):
  raw,lock,_=self.package();lock['archiveSHA256']='0'*64
  with self.assertRaises(ValueError):verified_binary(raw,lock)
 def test_changed_payload_rejected(self):
  raw,lock,_=self.package();lock['binarySHA256']='0'*64
  with self.assertRaises(ValueError):verified_binary(raw,lock)
 def test_wrong_target_rejected(self):
  raw,lock,_=self.package(machine=183)
  with self.assertRaises(ValueError):verified_binary(raw,lock)
 def test_extra_file_rejected(self):
  raw,lock,_=self.package(extra=True)
  with self.assertRaises(ValueError):verified_binary(raw,lock)
