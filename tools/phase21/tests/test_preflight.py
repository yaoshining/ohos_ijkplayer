from pathlib import Path
import importlib.util,os,shutil,subprocess,tempfile,unittest
R=Path(__file__).resolve().parents[1]
class ActualPreflight(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  pc=subprocess.run(['pkg-config','--cflags','--libs','libavutil'],capture_output=True,text=True)
  if pc.returncode:raise unittest.SkipTest('实际libavutil头/库尚未构建；native完整栈后必须再次运行')
  cls.tmp=tempfile.TemporaryDirectory();root=Path(cls.tmp.name);cls.exe=root/'preflight'
  src=root/'main.c';src.write_text('#include "integration.h"\n#include <stdio.h>\nint main(int argc,char**v){if(argc!=5)return 2;struct p21_config c={v[1],v[2],v[3],v[4]};struct p21_error e={0};int rc=p21_validate(&c,&e);printf("%s %d\\n",e.stage,e.code);return rc?1:0;}\n')
  subprocess.run(['cc','-std=c11','-Wall','-Wextra','-Werror','-I'+str(R),str(src),str(R/'preflight.c'),*pc.stdout.split(),'-o',str(cls.exe)],check=True)
  s=importlib.util.spec_from_file_location('p21res',R/'resources.py');cls.res=importlib.util.module_from_spec(s);s.loader.exec_module(cls.res)
 @classmethod
 def tearDownClass(cls):cls.tmp.cleanup()
 def check(self,mutate,expected):
  with tempfile.TemporaryDirectory() as t:
   root=Path(t).resolve()/'case';d=self.res.prepare(root);mutate(root,d)
   result=subprocess.run([str(self.exe),*d.values()],capture_output=True,text=True);self.assertEqual(result.returncode,expected,result.stdout+result.stderr)
 def test_fixed_font(self):self.check(lambda r,d:None,0)
 def test_readonly_fonts(self):self.check(lambda r,d:(r/'resources/fonts').chmod(0o555),0)
 def test_missing_directory(self):self.check(lambda r,d:(r/'state/private').rmdir(),1)
 def test_wrong_path_type(self):self.check(lambda r,d:d.update(state_root=str(r/'smb.conf')),1)
 def test_relative_path(self):self.check(lambda r,d:d.update(config_file='smb.conf'),1)
 def test_repeated_slash(self):self.check(lambda r,d:d.update(cache_root=str(r)+'//cache'),1)
 def test_dot_path(self):self.check(lambda r,d:d.update(resource_root=str(r)+'/./resources'),1)
 def test_corrupt_font(self):self.check(lambda r,d:(r/'resources/fonts/font1.ttf').write_bytes(b'bad'),1)
 def test_missing_font(self):self.check(lambda r,d:(r/'resources/fonts/font1.ttf').unlink(),1)
 def test_unreadable_font(self):self.check(lambda r,d:(r/'resources/fonts/font1.ttf').chmod(0),1)
 def test_unwritable_cache(self):self.check(lambda r,d:(r/'cache/demux').chmod(0o500),1)
 def test_extra_font(self):self.check(lambda r,d:shutil.copyfile(r/'resources/fonts/font1.ttf',r/'resources/fonts/extra.ttf'),1)
 def test_symlink_font(self):
  def mutate(r,d):p=r/'resources/fonts/font1.ttf';p.rename(r/'saved.ttf');p.symlink_to(r/'saved.ttf')
  self.check(mutate,1)
