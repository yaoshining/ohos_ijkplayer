"""真实静态链接依赖回归及AArch64能力表审计；不执行目标设备代码。"""
import hashlib,importlib.util,json,os,re,shlex,shutil,struct,subprocess,tempfile,unittest
from pathlib import Path
HERE=Path(__file__).parents[1]

def module():
    s=importlib.util.spec_from_file_location('features',HERE/'verify-dependency-features.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m

def elf_curve_fixture(ids=(5,1,2),supported=True):
    # GnuTLS3.8.7 ARM64 LP64: name/oid pointers, id at16, supported at36, stride48.
    table=b''.join(bytes(16)+struct.pack('<I',i)+bytes(16)+bytes([supported])+bytes(11) for i in ids)+bytes(48)
    strings=b'\0ecc_curves\0';names=b'\0.shstrtab\0.data\0.symtab\0.strtab\0'
    symbol=bytes(24)+struct.pack('<IBBHQQ',1,1,0,2,0,len(table))
    sections=[(1,3,0,names,0,0),(11,1,3,table,0,0),(17,2,0,symbol,4,24),(25,3,0,strings,0,0)]
    data=bytearray(64);headers=[bytes(64)]
    for n,t,f,payload,link,entry in sections:
        off=len(data);data.extend(payload);headers.append(struct.pack('<IIQQQQIIQQ',n,t,f,0,off,len(payload),link,0,8,entry))
    off=len(data);data.extend(b''.join(headers));data[:64]=struct.pack('<16sHHIQQQIHHHHHH',b'\x7fELF\x02\x01\x01'+bytes(9),1,183,1,0,0,off,0,64,0,0,64,5,1)
    return bytes(data)

class RecipeConfigure(unittest.TestCase):
    def setup_chain(self,root):
        prefix=root/'prefix';(prefix/'lib').mkdir(parents=True);work=root/'work';(work/'gnutls-3.8.7').mkdir(parents=True);(work/'gmp-6.3.0').mkdir()
        cc=shutil.which('cc');ar=shutil.which('ar');self.assertTrue(cc and ar)
        for name,source in [('gmp','int dependency(void){return 7;}'),('hogweed','extern int dependency(void); int nettle_get_secp_192r1(void){return dependency();}'),('nettle','int unused_nettle(void){return 0;}')]:
            src=root/(name+'.c');obj=root/(name+'.o');src.write_text(source);subprocess.run([cc,'-c',str(src),'-o',str(obj)],check=True);subprocess.run([ar,'rcs',str(prefix/'lib'/('lib'+name+'.a')),str(obj)],check=True)
        bin=root/'bin';bin.mkdir();make=bin/'make';make.write_text('#!/bin/sh\nexit 0\n');make.chmod(0o755)
        probe=root/'probe.c';probe.write_text('extern int nettle_get_secp_192r1(void); int main(void){return nettle_get_secp_192r1()!=7;}\n')
        config=work/'gnutls-3.8.7/configure';config.write_text('#!'+shutil.which('python3')+'\n'+'''import sys,subprocess,shlex,json,os
from pathlib import Path
args=dict(x.split('=',1) for x in sys.argv[1:] if '=' in x)
Path('received.json').write_text(json.dumps(args))
p=subprocess.run([os.environ['TEST_CC'],os.environ['TEST_PROBE'],*shlex.split(args['HOGWEED_LIBS']),'-o',os.environ['TEST_RESULT']])
if p.returncode:sys.exit(p.returncode)
Path('config.h').write_text('#define ENABLE_NON_SUITEB_CURVES 1\\n')
''');config.chmod(0o755)
        cfg=work/'gmp-6.3.0/configure';cfg.write_text('#!'+shutil.which('python3')+'\nimport sys,json\nfrom pathlib import Path\nPath("received.json").write_text(json.dumps(sys.argv[1:]))\n');cfg.chmod(0o755)
        env=dict(os.environ,PATH=str(bin)+os.pathsep+os.environ['PATH'],WORK_DIR=str(work),PREFIX=str(prefix),HOST_TRIPLET='test-native',JOBS='1',TEST_CC=cc,TEST_PROBE=str(probe),TEST_RESULT=str(root/'probe'))
        return env,work,prefix
    def run_function(self,name,env):
        function=re.search(name+r'\(\) \{.*?\n\}',(HERE/'build-libsmbclient.sh').read_text(),re.S).group()
        return subprocess.run(['bash','-c','set -e; log() { :; }; '+function+'\n'+name],env=env,text=True,capture_output=True)
    def test_gnutls_configure_links_full_transitive_chain(self):
        with tempfile.TemporaryDirectory() as t:
            env,work,prefix=self.setup_chain(Path(t));r=self.run_function('build_gnutls',env);self.assertEqual(r.returncode,0,r.stderr)
            self.assertIn('ENABLE_NON_SUITEB_CURVES 1',(work/'gnutls-3.8.7/config.h').read_text())
    def test_missing_gmp_archive_fails_actual_configure_link(self):
        with tempfile.TemporaryDirectory() as t:
            env,work,prefix=self.setup_chain(Path(t));(prefix/'lib/libgmp.a').unlink();r=self.run_function('build_gnutls',env);self.assertNotEqual(r.returncode,0)
    def test_omitted_gmp_fails_actual_link(self):
        with tempfile.TemporaryDirectory() as t:
            env,work,prefix=self.setup_chain(Path(t));p=subprocess.run([env['TEST_CC'],env['TEST_PROBE'],'-L'+str(prefix/'lib'),'-lhogweed','-lnettle','-o',env['TEST_RESULT']],capture_output=True);self.assertNotEqual(p.returncode,0)
    def test_gmp_configure_restores_baseline_options_keeps_pic(self):
        with tempfile.TemporaryDirectory() as t:
            env,work,prefix=self.setup_chain(Path(t));r=self.run_function('build_gmp',env);self.assertEqual(r.returncode,0,r.stderr);args=json.loads((work/'gmp-6.3.0/received.json').read_text())
            for flag in ['--disable-assembly','--without-readline','--with-pic']:self.assertIn(flag,args)

class TargetCapabilities(unittest.TestCase):
    def test_real_table_ids_not_arbitrary_strings(self):
        m=module();rows=m.curve_entries(elf_curve_fixture());self.assertTrue(m.require_curves(rows));self.assertEqual(rows[0]['id'],5)
    def test_missing_curve_despite_name_bytes_rejected(self):
        m=module();rows=m.curve_entries(elf_curve_fixture(ids=(2,))+b'SECP192R1\0SECP224R1\0')
        with self.assertRaises(ValueError):m.require_curves(rows)
    def test_disabled_curve_rejected(self):
        m=module()
        with self.assertRaises(ValueError):m.require_curves(m.curve_entries(elf_curve_fixture(supported=False)))
    def test_macro_contract_rejects_silent_reduction(self):
        m=module();good='#define NO_ASM 1\n#define GMP_MPARAM_H_SUGGEST "./mpn/generic/gmp-mparam.h"\n';gnutls='#define ENABLE_NON_SUITEB_CURVES 1\n'
        self.assertTrue(m.check_macros(good,gnutls))
        for a,b in [(good.replace('NO_ASM 1','NO_ASM 0'),gnutls),(good,''),(good.replace('generic','arm64'),gnutls)]:
            with self.assertRaises(ValueError):m.check_macros(a,b)
    def test_malformed_object_rejected(self):
        with self.assertRaises(ValueError):module().curve_entries(elf_curve_fixture()[:-1])
if __name__=='__main__':unittest.main()
