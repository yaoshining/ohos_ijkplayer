"""正式 SDK 门禁必须拒绝缺闭包/非重复/未锁输入，诊断产物单独保留。"""
from pathlib import Path
import importlib.util
import unittest
import sys
sys.dont_write_bytecode=True
spec=importlib.util.spec_from_file_location('gate',Path(__file__).parents[1]/'ci-gate.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
class GateTest(unittest.TestCase):
    def valid(self):return {'artifactKind':'source-build','deviceAcceptanceStatus':'pending','staticDependencies':{'fullyVerified':True,'rebuiltFromSource':True}}, {'allMatch':True,'libraryCount':6}, {'sourceArchiveVerified':True,'patchesVerified':True,'toolchainArchiveVerified':True,'hostToolsVerified':True}
    def test_complete_inputs_pass(self):self.assertEqual(m.failures(*self.valid()),[])
    def test_cached_closure_blocks(self):
        s,r,i=self.valid();s['staticDependencies']['fullyVerified']=False
        self.assertTrue(m.failures(s,r,i))
    def test_unpinned_host_tools_block(self):
        s,r,i=self.valid();i['hostToolsVerified']=False
        self.assertTrue(m.failures(s,r,i))
    def test_nonrepeatable_blocks(self):
        s,r,i=self.valid();r['allMatch']=False
        self.assertTrue(m.failures(s,r,i))
    def test_missing_input_hash_blocks(self):
        s,r,i=self.valid();i.pop('toolchainArchiveVerified')
        self.assertTrue(m.failures(s,r,i))
    def test_incomplete_library_comparison_blocks(self):
        s,r,i=self.valid();r['libraryCount']=5
        self.assertTrue(m.failures(s,r,i))
    def test_import_cannot_pass_as_source_build(self):
        s,r,i=self.valid();s['artifactKind']='imported-baseline'
        self.assertTrue(m.failures(s,r,i))
if __name__=='__main__':unittest.main()
