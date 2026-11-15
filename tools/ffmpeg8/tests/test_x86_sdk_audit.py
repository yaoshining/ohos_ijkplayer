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


class PackagingTests(unittest.TestCase):
    def test_pkgconfig_relocation(self):
        good = 'prefix=${pcfiledir}/../..\nexec_prefix=${prefix}\nlibdir=${exec_prefix}/lib\nincludedir=${prefix}/include\n'
        audit.check_pkgconfig(good, Path('/sdk'))
        for bad in [good.replace('${exec_prefix}/lib', '/outside/lib'),
                    good.replace('${prefix}/include', '/outside/include'),
                    good.replace('exec_prefix=${prefix}', 'exec_prefix=/outside')]:
            with self.assertRaisesRegex(ValueError, '不可重定位'):
                audit.check_pkgconfig(bad, Path('/sdk'))

    def load_package(self):
        spec = importlib.util.spec_from_file_location('package_x86', path.parent / 'package-x86-sdk.py')
        package = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(package)
        return package

    def test_copied_absolute_library_link_rejected(self):
        import tempfile
        package = self.load_package()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            sdk = root / 'original'
            (sdk / 'lib').mkdir(parents=True)
            target = sdk / 'lib/libavcodec.so.62.1'
            target.write_bytes(b'fixture')
            (sdk / 'lib/libavcodec.so.62').symlink_to(target)
            with self.assertRaisesRegex(ValueError, '库链接逃出 SDK'):
                package.copy_and_audit(sdk, root / 'copied', root / 'ndk')
            self.assertTrue(target.exists())

    def test_spdx_missing_or_dangling_describes_rejected(self):
        import copy
        package = self.load_package()
        document = {'SPDXID': 'SPDXRef-DOCUMENT',
                    'packages': [{'SPDXID': 'SPDXRef-A'}, {'SPDXID': 'SPDXRef-B'}],
                    'documentDescribes': ['SPDXRef-A', 'SPDXRef-B'],
                    'relationships': [{'spdxElementId': 'SPDXRef-DOCUMENT',
                                       'relationshipType': 'DESCRIBES', 'relatedSpdxElement': name}
                                      for name in ['SPDXRef-A', 'SPDXRef-B']]}
        package.check_sbom_relationships(document)
        for field in ['documentDescribes', 'relationships']:
            broken = copy.deepcopy(document)
            broken[field].pop()
            with self.assertRaises(ValueError):
                package.check_sbom_relationships(broken)
        document['relationships'][0]['relatedSpdxElement'] = 'SPDXRef-unknown'
        with self.assertRaises(ValueError):
            package.check_sbom_relationships(document)


if __name__ == '__main__':
    unittest.main()
