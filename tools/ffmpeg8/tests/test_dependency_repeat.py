"""真实文件清单与构建前工具锁的失败路径。"""
import importlib.util,json,tempfile,unittest
from pathlib import Path

def module(name):
    spec=importlib.util.spec_from_file_location(name,Path(__file__).parents[1]/(name+'.py'));m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m

class HostLockTests(unittest.TestCase):
    def test_lock_a_cannot_build_ndk_b(self):
        m=module('host-lock')
        with tempfile.TemporaryDirectory() as t:
            a=Path(t)/'a';a.mkdir();b=Path(t)/'b';b.mkdir();recipe=Path(t)/'recipe';recipe.mkdir()
            lock={'ndkRoot':str(a),'recipeRoot':str(recipe),'recipeFiles':[]}
            with self.assertRaises(ValueError):m.verify_binding(lock,b,recipe)
    def test_extra_recipe_file_rejected(self):
        m=module('host-lock')
        with tempfile.TemporaryDirectory() as t:
            root=Path(t);recipe=root/'recipe';recipe.mkdir();(recipe/'injected.sh').write_text('bad')
            lock={'ndkRoot':str(root),'recipeRoot':str(recipe),'recipeFiles':[]}
            with self.assertRaises(ValueError):m.verify_binding(lock,root,recipe)
    def test_host_generator_uses_captured_path(self):
        text=(Path(__file__).parents[1]/'build-libsmbclient.sh').read_text()
        self.assertIn('NATIVE_BUILD_PATH="$PATH"',text)
        self.assertIn('PATH="$PREFIX/bin:$NATIVE_BUILD_PATH"',text)
    def test_modified_tool_rejected(self):
        m=module('host-lock')
        with tempfile.TemporaryDirectory() as t:
            f=Path(t)/'tool';f.write_text('old')
            lock={'files':[m.record(f)],'environment':{}}
            m.verify(lock)
            f.write_text('new')
            with self.assertRaises(ValueError):m.verify(lock)
    def test_path_resolution_drift_rejected(self):
        m=module('host-lock')
        with self.assertRaises(ValueError):m.verify({'files':[],'environment':{},'commands':[{'name':'python3','path':'/no/such/python','sha256':'0'*64}]})
    def test_missing_file_rejected(self):
        m=module('host-lock')
        with self.assertRaises(ValueError):m.verify({'files':[{'path':'/no/such/tool','sha256':'0'*64}],'environment':{}})

class RepeatTests(unittest.TestCase):
    def make(self,root):
        m=module('dependency-repeat')
        for rel in m.DELIVERED_LIBS+['include/a.h','lib/pkgconfig/a.pc']:
            f=root/rel;f.parent.mkdir(parents=True,exist_ok=True);f.write_text('same')
        return m
    def test_actual_inventory_equal_then_tamper(self):
        with tempfile.TemporaryDirectory() as t:
            a=Path(t)/'a';b=Path(t)/'b';m=self.make(a);self.make(b)
            self.assertTrue(m.compare(a,b)['allMatch'])
            (b/'include/a.h').write_text('changed')
            self.assertFalse(m.compare(a,b)['allMatch'])
    def test_missing_static_library_fails(self):
        with tempfile.TemporaryDirectory() as t:
            a=Path(t)/'a';b=Path(t)/'b';m=self.make(a);self.make(b)
            (b/m.DELIVERED_LIBS[0]).unlink()
            with self.assertRaises(ValueError):m.compare(a,b)
    def test_extra_delivered_header_fails(self):
        with tempfile.TemporaryDirectory() as t:
            a=Path(t)/'a';b=Path(t)/'b';m=self.make(a);self.make(b)
            (b/'include/extra.h').write_text('extra')
            self.assertFalse(m.compare(a,b)['allMatch'])
    def test_same_root_cannot_prove_independence(self):
        with tempfile.TemporaryDirectory() as t:
            a=Path(t);m=self.make(a)
            with self.assertRaises(ValueError):m.compare(a,a)
if __name__=='__main__':unittest.main()
