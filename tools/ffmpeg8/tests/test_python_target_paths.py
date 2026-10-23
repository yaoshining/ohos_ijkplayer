"""实际shell配置入口与AArch64路径指针，不用任意字符串替代目标值。"""
import importlib.util,os,re,subprocess,tempfile,unittest,shutil
from pathlib import Path
HERE=Path(__file__).parents[1];EXPECTED='/usr/local/samba/lib/python3/site-packages'
def feature():
 s=importlib.util.spec_from_file_location('python_paths',HERE/'verify-dependency-features.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
class TargetPythonPaths(unittest.TestCase):
 def test_target_configure_overrides_host_python_environment(self):
  text=(HERE/'build-libsmbclient.sh').read_text();func=re.search(r'configure_samba\(\) \{.*?\n\}',text,re.S).group()
  with tempfile.TemporaryDirectory() as t:
   r=Path(t);(r/'bin').mkdir();(r/'bin/asn1_compile').touch();(r/'bin/compile_et').touch();c=r/'configure';c.write_text('#!/bin/sh\nprintf "%s\\n" "$@" > arguments\n');c.chmod(0o755)
   env=dict(os.environ,SAMBA_DIR=str(r),HOST_TRIPLET='aarch64-linux-ohos',PYTHONDIR='/host/python',PYTHONARCHDIR='/host/arch')
   subprocess.run(['bash','-c','set -e; log(){ :; }; '+func+'\nconfigure_samba'],env=env,check=True)
   args=(r/'arguments').read_text().splitlines();self.assertIn('--disable-python',args);self.assertIn('--pythondir='+EXPECTED,args);self.assertIn('--pythonarchdir='+EXPECTED,args)
 def object(self,r,value,extra=''):
  source=r/'path.c';obj=r/'path.o';source.write_text('const char *dyn_PYTHONDIR="'+value+'";const char *dyn_PYTHONARCHDIR="'+value+'";'+extra)
  subprocess.run([shutil.which('clang'),'--target=aarch64-linux-gnu','-c',str(source),'-o',str(obj)],check=True);return obj.read_bytes()
 def test_actual_pointer_and_disabled_state(self):
  with tempfile.TemporaryDirectory() as t:
   data=self.object(Path(t),EXPECTED);m=feature();self.assertTrue(m.verify_python_paths(data,{'disable_python':True})['disabled'])
 def test_host_pointer_rejected_despite_target_decoy_string(self):
  with tempfile.TemporaryDirectory() as t:
   data=self.object(Path(t),'/opt/homebrew/python','const char *decoy="'+EXPECTED+'";')
   with self.assertRaises(ValueError):feature().verify_python_paths(data,{'disable_python':True})
 def test_empty_pointer_rejected(self):
  with tempfile.TemporaryDirectory() as t:
   with self.assertRaises(ValueError):feature().verify_python_paths(self.object(Path(t),''),{'disable_python':True})
 def test_python_enabled_or_missing_state_rejected(self):
  with tempfile.TemporaryDirectory() as t:
   data=self.object(Path(t),EXPECTED)
   for env in [{'disable_python':False},{}]:
    with self.assertRaises(ValueError):feature().verify_python_paths(data,env)
if __name__=='__main__':unittest.main()

class FinalRuntimePythonPaths(unittest.TestCase):
 def elf_fixture(self,path,with_pointers=True,host_path=False):
  import struct
  strings=b'\0.shstrtab\0.rodata\0.data\0.rela.dyn\0';rodata=EXPECTED.encode()+b'\0'+(b'/opt/homebrew/lib/python3.14/site-packages\0' if host_path else b'');payloads=[b'',strings,rodata,b'\0'*16,(struct.pack('<QQq',0x3000,1027,0x2000)+struct.pack('<QQq',0x3008,1027,0x2000)) if with_pointers else b''];offset=64+5*64;headers=[b'\0'*64];body=b''
  for i,(name,typ,flags,addr,entry) in enumerate([('.shstrtab',3,0,0,0),('.rodata',1,2,0x2000,0),('.data',1,3,0x3000,0),('.rela.dyn',4,2,0x4000,24)],1):
   payload=payloads[i];headers.append(struct.pack('<IIQQQQIIQQ',strings.index(name.encode()),typ,flags,addr,offset,len(payload),0,0,8,entry));body+=payload;offset+=len(payload)
  ident=b'\x7fELF\x02\x01\x01'+b'\0'*9;header=struct.pack('<16sHHIQQQIHHHHHH',ident,3,183,1,0,0,64,0,64,0,0,64,5,1);path.write_bytes(header+b''.join(headers)+body)
 def test_target_relocation_pointers_accepted(self):
  with tempfile.TemporaryDirectory() as t:
   p=Path(t)/'runtime.so';self.elf_fixture(p);self.assertEqual(len(feature().verify_python_runtime(p)['relativePointerLocations']),2)
 def test_decoy_target_string_without_pointers_rejected(self):
  with tempfile.TemporaryDirectory() as t:
   p=Path(t)/'runtime.so';self.elf_fixture(p,with_pointers=False)
   with self.assertRaises(ValueError):feature().verify_python_runtime(p)
 def test_host_path_residual_rejected_even_with_target_pointers(self):
  with tempfile.TemporaryDirectory() as t:
   p=Path(t)/'runtime.so';self.elf_fixture(p,host_path=True)
   with self.assertRaises(ValueError):feature().verify_python_runtime(p)
