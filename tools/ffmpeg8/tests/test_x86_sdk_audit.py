"""x86 SDK 不允许混入宿主/ARM64、缺少依赖或伪造硬解能力。"""
import importlib.util
from pathlib import Path
import struct
import unittest

path = Path(__file__).resolve().parents[1] / 'audit-x86-sdk.py'
spec = importlib.util.spec_from_file_location('audit_x86', path)
audit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit)


class ContractTests(unittest.TestCase):
    def test_target_header(self):
        data = bytearray(64)
        data[:7] = b'\x7fELF\x02\x01\x01'
        struct.pack_into('<H', data, 18, 62)
        audit.check_header(bytes(data))
        struct.pack_into('<H', data, 18, 183)
        with self.assertRaises(ValueError):
            audit.check_header(bytes(data))
        with self.assertRaises(ValueError):
            audit.check_header(b'host Mach-O')

    def test_missing_dependency(self):
        audit.check_needed(['libc.so', 'libavutil.so.60'], {'libc.so', 'libavutil.so.60'})
        for name in ['libc.so.6', 'libunknown.so']:
            with self.assertRaises(ValueError):
                audit.check_needed([name], {'libc.so'})

    def test_no_fake_ohcodec(self):
        audit.check_software_exports({'avcodec_version'})
        with self.assertRaises(ValueError):
            audit.check_software_exports({'av_ohcodec_release_buffer'})


if __name__ == '__main__':
    unittest.main()
