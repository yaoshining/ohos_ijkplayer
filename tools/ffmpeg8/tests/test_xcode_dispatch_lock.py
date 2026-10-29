"""真实临时文件与转发解析：launcher不变不能掩盖实际执行文件/资源漂移。"""
import importlib.util,os,tempfile,unittest,contextlib
from pathlib import Path
from unittest.mock import patch
HERE=Path(__file__).parents[1]
def module(n):
 s=importlib.util.spec_from_file_location(n,HERE/(n+'.py'));m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
class XcodeDispatch(unittest.TestCase):
 @contextlib.contextmanager
 def fixture(self):
  with tempfile.TemporaryDirectory() as t:
   r=Path(t);ndk=r/'ndk';recipe=r/'recipe';ndk.mkdir();recipe.mkdir();stub=r/'launcher';stub.write_text('#!/bin/sh\necho stub\n');stub.chmod(0o755);select=r/'select';select.write_text('selector');xcrun=r/'xcrun';xcrun.write_text('resolver');real=r/'Xcode/usr/bin';real.mkdir(parents=True);data=real.parent/'share/bison';data.mkdir(parents=True);(data/'yacc.c').write_text('skeleton')
   for n in ['flex','bison','m4','clang','clang++','ld']:(real/n).write_text('actual '+n);(real/n).chmod(0o755)
   m=module('host-lock');paths={n:str(real/n) for n in ['flex','bison','m4','clang','clang++','ld']};state={'developer':str(r/'Xcode')}
   def query(cmd,**kw):
    if '--find' in cmd:return paths[cmd[-1]]+'\n'
    if '-p' in cmd:return state['developer']+'\n'
    raise AssertionError(cmd)
   with patch.object(m,'COMMANDS',['flex','bison','m4']),patch.object(m.platform,'platform',return_value='Darwin-test'),patch.object(m.platform,'system',return_value='Darwin'),patch.object(m.shutil,'which',return_value=str(stub)),patch.object(m.subprocess,'check_output',side_effect=query),patch.object(m,'DISPATCHER_REFERENCE',str(stub),create=True),patch.object(m,'XCRUN',str(xcrun),create=True),patch.object(m,'XCODE_SELECT',str(select),create=True):
    yield m,m.capture(ndk,recipe,'test'),real,data,paths,state
 def test_unchanged_launchers_cannot_hide_actual_tool_change(self):
  with self.fixture() as (m,lock,real,data,paths,state):
   m.verify(lock);(real/'flex').write_text('changed actual tool')
   with self.assertRaises(ValueError):m.verify(lock)
 def test_missing_actual_tool_rejected(self):
  with self.fixture() as (m,lock,real,data,paths,state):
   (real/'m4').unlink()
   with self.assertRaises(ValueError):m.verify(lock)
 def test_new_resource_file_rejected(self):
  with self.fixture() as (m,lock,real,data,paths,state):
   (data/'new.m4').write_text('injected')
   with self.assertRaises(ValueError):m.verify(lock)
 def test_changed_resource_rejected(self):
  with self.fixture() as (m,lock,real,data,paths,state):
   (data/'yacc.c').write_text('changed')
   with self.assertRaises(ValueError):m.verify(lock)
 def test_changed_selector_rejected(self):
  with self.fixture() as (m,lock,real,data,paths,state):
   state['developer']='different Xcode'
   with self.assertRaises(ValueError):m.verify(lock)
 def test_resolution_path_change_rejected(self):
  with self.fixture() as (m,lock,real,data,paths,state):
   other=real/'other';other.write_bytes((real/'flex').read_bytes());other.chmod(0o755);paths['flex']=str(other)
   with self.assertRaises(ValueError):m.verify(lock)
 def test_selectors_survive_controlled_environment(self):
  m=module('run-dependency-build')
  with patch.dict(os.environ,{'DEVELOPER_DIR':'/chosen/Xcode','SDKROOT':'/chosen/SDK','TOOLCHAINS':'chosen'}):
   env=m.controlled_environment(Path('/ndk'),Path('/new'),Path('/cache'),'1','a'*64)
  for k,v in [('DEVELOPER_DIR','/chosen/Xcode'),('SDKROOT','/chosen/SDK'),('TOOLCHAINS','chosen')]:self.assertEqual(env.get(k),v)
if __name__=='__main__':unittest.main()

class AdditionalDispatchBoundaries(unittest.TestCase):
 fixture=XcodeDispatch.fixture
 def test_removed_resource_rejected(self):
  with self.fixture() as (m,lock,real,data,paths,state):
   (data/'yacc.c').unlink()
   with self.assertRaises(ValueError):m.verify(lock)
 def test_non_dispatch_tool_keeps_path_choice(self):
  with self.fixture() as (m,lock,real,data,paths,state):
   direct=real/'custom-flex';direct.write_text('#!/bin/sh\necho direct\n');direct.chmod(0o755)
   with patch.object(m,'COMMANDS',['flex']),patch.object(m.shutil,'which',return_value=str(direct)):
    other=m.capture(real,data,'test');self.assertEqual(other['commands'][0]['path'],str(direct.resolve()));self.assertEqual(other['xcodeDispatch']['resolvedCommands'],[]);m.verify(other)

class ResourceDirectoryLinks(unittest.TestCase):
 def test_valid_directory_link_binds_target_and_contents(self):
  m=module('host-lock')
  with tempfile.TemporaryDirectory() as t:
   r=Path(t);a=r/'a';a.mkdir();(a/'file').write_text('first');(r/'alias').symlink_to(a,target_is_directory=True);before=m.directory_record(r);(a/'file').write_text('second');self.assertNotEqual(before,m.directory_record(r))
 def test_resource_link_cycle_and_dangling_rejected(self):
  m=module('host-lock')
  with tempfile.TemporaryDirectory() as t:
   r=Path(t);link=r/'alias';link.symlink_to(r,target_is_directory=True)
   with self.assertRaises(ValueError):m.directory_record(r)
   link.unlink();link.symlink_to(r/'missing')
   with self.assertRaises(ValueError):m.directory_record(r)
