import ctypes as C, errno, os, pathlib, shutil, subprocess, tempfile, threading, unittest
ROOT=pathlib.Path(__file__).resolve().parents[1]
class Config(C.Structure):
 _fields_=[('struct_size',C.c_size_t)]+[(k,C.c_char_p) for k in ['config_file','state_root','cache_root','resource_root']]
class Runtime(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.build=tempfile.TemporaryDirectory();cls.so=pathlib.Path(cls.build.name)/'runtime.so'
  subprocess.run(['cc','-shared','-fPIC','-pthread','-DRT_TESTING','-Wall','-Wextra','-Werror','-I',str(ROOT/'runtime'),str(ROOT/'runtime/smb_runtime.c'),'-o',str(cls.so)],check=True)
 @classmethod
 def tearDownClass(cls):cls.build.cleanup()
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.root=pathlib.Path(self.tmp.name).resolve();p=self.root/'unique.so';shutil.copyfile(self.so,p);self.lib=C.CDLL(str(p),use_errno=True)
  for n in ['s/private','s/state','s/lock','c','r']:(self.root/n).mkdir(parents=True,exist_ok=True)
  self.file=self.root/'smb.conf';self.file.write_text('[global]\nworkgroup = EXPLICIT\n')
  self.cfg=Config(C.sizeof(Config),*[os.fsencode(self.root/n) for n in ['smb.conf','s','c','r']]);self.lib.ohcodec_smb_runtime_configure_internal.argtypes=[C.POINTER(Config)];self.lib.rt_dyn.argtypes=[C.c_char_p];self.lib.rt_dyn.restype=C.c_char_p;self.lib.rt_parameter.argtypes=[C.c_char_p];self.lib.rt_parameter.restype=C.c_char_p
 def tearDown(self):self.tmp.cleanup()
 def configure(self,c=None):return self.lib.ohcodec_smb_runtime_configure_internal(C.byref(c or self.cfg))
 def test_01_mapping_and_no_side_effects(self):
  before=set(self.root.rglob('*'));env=dict(os.environ);self.assertEqual(self.configure(),0);self.assertEqual(set(self.root.rglob('*')),before);self.assertEqual(dict(os.environ),env)
  for key,path in {'CONFIGFILE':'smb.conf','PRIVATE_DIR':'s/private','STATEDIR':'s/state','LOCKDIR':'s/lock','CACHEDIR':'c','CODEPAGEDIR':'r/codepages','LMHOSTSFILE':'r/etc/lmhosts','MODULESDIR':'r/modules'}.items():self.assertEqual(self.lib.rt_dyn(key.encode()),os.fsencode(self.root/path))
  self.assertIsNone(self.lib.rt_dyn(b'LIBDIR'));self.assertIsNone(self.lib.rt_dyn(b'NCALRPCDIR'));self.assertIsNone(self.lib.rt_dyn(b'PYTHONDIR'));self.assertEqual(self.lib.rt_parameter(b'lock directory'),os.fsencode(self.root/'s/lock'))
 def test_02_same_and_conflicting(self):
  self.assertEqual(self.configure(),0);self.assertEqual(self.configure(),0);self.cfg.resource_root=os.fsencode(self.root/'s');self.assertEqual(self.configure(),-1);self.assertEqual(C.get_errno(),errno.EBUSY)
 def test_03_invalid_struct(self):
  self.cfg.struct_size=0;self.assertEqual(self.configure(),-1);self.assertEqual(C.get_errno(),errno.EINVAL)
 def test_04_relative_empty_and_parent_paths(self):
  for v in [b'',b'relative',os.fsencode(self.root/'s/../s'),os.fsencode(self.root)+'//s'.encode(),b'/tmp/%U',b'/tmp/a\nb']:
   self.cfg.state_root=v;self.assertEqual(self.configure(),-1);self.assertEqual(C.get_errno(),errno.EINVAL)
 def test_05_missing_and_wrong_type(self):
  self.file.unlink();self.assertEqual(self.configure(),-1);self.assertEqual(C.get_errno(),errno.ENOENT);self.file.mkdir();self.assertEqual(self.configure(),-1)
 def test_06_symlink(self):
  q=self.root/'alias';q.symlink_to(self.root/'s',target_is_directory=True);self.cfg.state_root=os.fsencode(q);self.assertEqual(self.configure(),-1);self.assertEqual(C.get_errno(),errno.EINVAL)
 def test_07_permission_and_retry(self):
  q=self.root/'s/lock';q.chmod(0o500);self.assertEqual(self.configure(),-1);self.assertEqual(C.get_errno(),errno.EACCES);q.chmod(0o700);self.assertEqual(self.configure(),0)
 def test_08_allocation_failure_atomicity(self):
  for n in range(18):
   self.lib.rt_test_fail_alloc_after(n);r=self.configure()
   if r==0:break
   self.assertEqual(C.get_errno(),errno.ENOMEM);self.assertIsNone(self.lib.rt_dyn(b'CONFIGFILE'))
  self.lib.rt_test_fail_alloc_after(-1);self.assertEqual(self.configure(),0)
 def test_09_legacy_freezes(self):
  self.assertEqual(self.lib.rt_lock(),0);self.assertEqual(self.lib.rt_begin(),0);self.lib.rt_unlock();self.assertEqual(self.configure(),-1);self.assertEqual(C.get_errno(),errno.EBUSY)
 def test_10_failure_closed(self):
  self.assertEqual(self.configure(),0);self.lib.rt_lock();self.lib.rt_fail();self.assertEqual(self.lib.rt_begin(),-1);self.lib.rt_unlock();self.assertEqual(self.configure(),-1);self.assertEqual(C.get_errno(),errno.EIO)
 def test_11_reentrant_rejected(self):
  self.assertEqual(self.lib.rt_lock(),0);self.assertEqual(self.lib.rt_lock(),-1);self.assertEqual(C.get_errno(),errno.EDEADLK);self.lib.rt_unlock();self.assertEqual(self.configure(),0)
 def test_12_pending_context_prevents_termination(self):
  self.configure();self.lib.rt_lock();self.lib.rt_begin();self.lib.rt_add_context();self.lib.rt_add_context();self.assertEqual(self.lib.rt_remove_context(),0);self.assertEqual(self.lib.rt_remove_context(),1);self.assertEqual(self.lib.rt_begin(),0);self.assertEqual(self.lib.rt_dyn(b'LOCKDIR'),os.fsencode(self.root/'s/lock'));self.lib.rt_unlock()
 def test_13_concurrent_same_configuration(self):
  results=[];threads=[threading.Thread(target=lambda:results.append(self.configure()))for _ in range(16)]
  for t in threads:t.start()
  for t in threads:t.join(5);self.assertFalse(t.is_alive())
  self.assertEqual(results,[0]*16)
 def test_14_config_permission(self):
  self.file.chmod(0);self.assertEqual(self.configure(),-1);self.assertEqual(C.get_errno(),errno.EACCES)
 def test_15_null_and_shortest_absolute_paths(self):
  self.assertEqual(self.lib.ohcodec_smb_runtime_configure_internal(None),-1);self.assertEqual(C.get_errno(),errno.EINVAL)
  for value in [None,b'/',b'/a']:
   self.cfg.state_root=value;self.assertEqual(self.configure(),-1);self.assertIn(C.get_errno(),[errno.EINVAL,errno.ENOENT])
 def test_16_derived_length_limit(self):
  self.cfg.resource_root=b'/'+b'a'*4094;self.assertEqual(self.configure(),-1);self.assertEqual(C.get_errno(),errno.EINVAL)
 def test_17_two_valid_conflicting_threads(self):
  (self.root/'other.conf').write_text('[global]\n');other=Config(C.sizeof(Config),os.fsencode(self.root/'other.conf'),self.cfg.state_root,self.cfg.cache_root,self.cfg.resource_root)
  gate=threading.Barrier(2);results=[]
  def work(c):
   gate.wait();r=self.configure(c);results.append((r,C.get_errno()))
  ts=[threading.Thread(target=work,args=(c,)) for c in [self.cfg,other]]
  for t in ts:t.start()
  for t in ts:t.join(5);self.assertFalse(t.is_alive())
  self.assertEqual(sorted(r for r,e in results),[-1,0]);self.assertEqual([e for r,e in results if r<0],[errno.EBUSY])
 def test_18_path_revalidated_before_reinitialization(self):
  self.assertEqual(self.configure(),0);self.assertEqual(self.lib.rt_validate_current(),0);self.file.unlink();self.assertEqual(self.lib.rt_validate_current(),-1);self.assertEqual(C.get_errno(),errno.ENOENT)
if __name__=='__main__':unittest.main()
