"""SMB 配置与硬解无关；x86 SDK 必须保留真实运行时合同。"""
import ctypes as C
import importlib.util
from pathlib import Path
import shutil
import tempfile
import unittest

TOOLS = Path(__file__).resolve().parents[2]

def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result

audit = module('x86_audit_smb', TOOLS / 'ffmpeg8/audit-x86-sdk.py')
runtime = module('arm_runtime_tests', TOOLS / 'phase20/tests/test_runtime.py')
lifecycle = module('arm_lifecycle_tests', TOOLS / 'phase20/tests/test_lifecycle.py')
Lifecycle = lifecycle.Lifecycle

class RuntimeContract(runtime.Runtime):
    def test_19_caller_strings_are_copied_before_context(self):
        buffers = [C.create_string_buffer(getattr(self.cfg, field))
                   for field in ['config_file', 'state_root', 'cache_root', 'resource_root']]
        config = runtime.Config(C.sizeof(runtime.Config),
                                *(C.cast(buf, C.c_char_p) for buf in buffers))
        self.assertEqual(self.configure(config), 0)
        saved = self.lib.rt_dyn(b'CONFIGFILE')
        for buf in buffers:
            buf[1] = b'Z'
        self.assertEqual(self.lib.rt_dyn(b'CONFIGFILE'), saved)
        self.assertEqual(self.configure(), 0)
        self.assertEqual(self.lib.rt_lock(), 0)
        self.assertEqual(self.lib.rt_begin(), 0)
        self.assertEqual(self.lib.rt_dyn(b'CONFIGFILE'), saved)
        self.assertEqual(self.lib.rt_parameter(b'cache directory'), self.cfg.cache_root)
        self.lib.rt_unlock()

class SdkContract(unittest.TestCase):
    def test_missing_header_export_and_mismatched_header_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            sdk = Path(temp)
            header = sdk / 'include/libavformat/ohcodec_smb_runtime.h'
            header.parent.mkdir(parents=True)
            symbols = {'ohcodec_smb_runtime_configure_v1'}
            with self.assertRaisesRegex(ValueError, 'SMB'):
                audit.check_smb_runtime(sdk, symbols)
            shutil.copyfile(TOOLS / 'phase20/runtime/smb_runtime.h', header)
            with self.assertRaisesRegex(ValueError, 'SMB'):
                audit.check_smb_runtime(sdk, set())
            audit.check_smb_runtime(sdk, symbols)
            header.write_text('/* missing ABI */')
            with self.assertRaisesRegex(ValueError, 'SMB'):
                audit.check_smb_runtime(sdk, symbols)

if __name__ == '__main__':
    unittest.main()
