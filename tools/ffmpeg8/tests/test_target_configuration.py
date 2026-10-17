"""实际编译/链接探测：宿主平台泄漏与仅有头文件的假阳性。"""
import importlib.util, os, shutil, subprocess, tempfile, types, unittest
from pathlib import Path
HERE=Path(__file__).parents[1]
PLATFORM='''def configure(conf):
    host_os = sys.platform
    host_os = sys.platform
    if 'linux' in host_os:
        conf.DEFINE('LINUX', 1)
    elif 'darwin' in host_os:
        conf.DEFINE('DARWINOS', 1)
    return host_os
'''
SOCKET='''def configure(conf):
    conf.CHECK_HEADERS('linux/sockios.h linux/ethtool.h')
    if (conf.CONFIG_SET('HAVE_LINUX_SOCKIOS_H') and \\
                    conf.CONFIG_SET('HAVE_LINUX_ETHTOOL_H')):
        conf.DEFINE('HAVE_ETHTOOL', 1)
'''
def patch(kind,text):
    p=HERE/'samba-target-config.py'
    if not p.exists():return text
    s=importlib.util.spec_from_file_location('target_config',p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return getattr(m,'patch_'+kind)(text)
class CompilerConf:
    def __init__(self,root,flags=()):self.root=root;self.flags=list(flags);self.defines={};self.env=types.SimpleNamespace(CROSS_COMPILE=True);self.results=[]
    def DEFINE(self,name,value):self.defines[name]=value
    def CONFIG_SET(self,name):return bool(self.defines.get(name))
    def CHECK_CODE(self,code,define=None,headers=None,addmain=True,**kwargs):
        source=(''.join('#include <'+n+'>\n' for n in (headers or '').split())+('int main(void){\n'+code+';\nreturn 0;}\n' if addmain else code))
        p=self.root/'probe.c';p.write_text(source)
        result=subprocess.run([shutil.which('cc'),'-Werror=implicit-function-declaration',*self.flags,'-I'+str(self.root),str(p),'-o',str(self.root/'probe')],capture_output=True)
        self.results.append(result.returncode)
        if result.returncode==0 and define:self.DEFINE(define,1)
        return result.returncode==0
    def CHECK_HEADERS(self,names):
        for n in names.split():
            if self.CHECK_CODE('',headers=n):self.DEFINE('HAVE_'+n.upper().replace('/','_').replace('.','_'),1)
class TargetConfiguration(unittest.TestCase):
    def run_config(self,kind,source,conf,host='darwin'):
        scope={'sys':types.SimpleNamespace(platform=host)};exec(patch(kind,source),scope);return scope['configure'](conf)
    def test_ohos_compiler_does_not_inherit_darwin(self):
        with tempfile.TemporaryDirectory() as t:
            c=CompilerConf(Path(t),['-D__OHOS__=1']);self.assertEqual(self.run_config('platform',PLATFORM,c),'ohos');self.assertNotIn('DARWINOS',c.defines);self.assertNotIn('LINUX',c.defines)
    def test_native_host_keeps_real_platform(self):
        with tempfile.TemporaryDirectory() as t:
            c=CompilerConf(Path(t),['-U__OHOS__']);c.env.CROSS_COMPILE=False;self.assertEqual(self.run_config('platform',PLATFORM,c),'darwin');self.assertEqual(c.defines['DARWINOS'],1)
    def headers(self,p,working):
        (p/'linux').mkdir();(p/'linux/sockios.h').write_text('#define SIOCETHTOOL 0x8946\n');(p/'linux/ethtool.h').write_text('struct ethtool_cmd {unsigned speed;};\n'+('static unsigned ethtool_cmd_speed(const struct ethtool_cmd *p){return p->speed;}\n' if working else ''))
    def test_headers_without_function_do_not_enable_ethtool(self):
        with tempfile.TemporaryDirectory() as t:
            p=Path(t);self.headers(p,False);c=CompilerConf(p);self.run_config('socket',SOCKET,c);self.assertTrue(c.CONFIG_SET('HAVE_LINUX_ETHTOOL_H'));self.assertFalse(c.CONFIG_SET('HAVE_ETHTOOL'))
    def test_real_function_enables_ethtool(self):
        with tempfile.TemporaryDirectory() as t:
            p=Path(t);self.headers(p,True);c=CompilerConf(p);self.run_config('socket',SOCKET,c);self.assertTrue(c.CONFIG_SET('HAVE_ETHTOOL'))
    def test_missing_header_does_not_enable_ethtool(self):
        with tempfile.TemporaryDirectory() as t:
            p=Path(t);self.headers(p,False);(p/'linux/ethtool.h').write_text('#error unavailable\n');c=CompilerConf(p);self.run_config('socket',SOCKET,c);self.assertFalse(c.CONFIG_SET('HAVE_ETHTOOL'))
if __name__=='__main__':unittest.main()

class ArtifactAlignment(unittest.TestCase):
    def features(self):
        s=importlib.util.spec_from_file_location('features_align',HERE/'verify-dependency-features.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
    def test_acceleration_requires_reference_and_definition(self):
        m=self.features()
        with self.assertRaises(ValueError):m.require_symbol({'symbols':[{'name':'register_aarch64_crypto','sectionIndex':0}]},'register_aarch64_crypto',defined=True)
        self.assertTrue(m.require_symbol({'symbols':[{'name':'register_aarch64_crypto','sectionIndex':2,'size':4,'type':2}]},'register_aarch64_crypto',defined=True))
    def test_actual_target_pointer_path_relocation(self):
        with tempfile.TemporaryDirectory() as t:
            p=Path(t);c=p/'p.c';obj=p/'p.o';c.write_text('const char *dyn_MODULESDIR="/usr/local/samba/lib";')
            subprocess.run([shutil.which('clang'),'--target=aarch64-linux-gnu','-c',str(c),'-o',str(obj)],check=True)
            m=self.features();self.assertEqual(m.elf_pointer_string(obj.read_bytes(),'dyn_MODULESDIR'),'/usr/local/samba/lib')
            with self.assertRaises(ValueError):m.elf_pointer_string(obj.read_bytes(),'dyn_MISSING')
            with self.assertRaises(ValueError):m.elf_pointer_string(obj.read_bytes()[:64],'dyn_MODULESDIR')
