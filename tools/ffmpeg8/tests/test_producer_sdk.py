"""交付摘要门禁行为回归；无需 NDK 或真实播放器。"""
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import sys
sys.dont_write_bytecode = True
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location('producer', Path(__file__).parents[1] / 'producer-sdk.py')
sdk = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sdk)

class ProducerTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        (self.root / 'lib').mkdir()
        self.file = self.root / 'lib/test.so'
        self.file.write_bytes(b'baseline')
        self.row = {'path': 'lib/test.so', 'sha256': hashlib.sha256(b'baseline').hexdigest(), 'sizeBytes': 8}

    def test_valid_inventory(self):
        sdk.check_files(self.root, [self.row])

    def test_tamper_same_size_rejected(self):
        self.file.write_bytes(b'BASELINE')
        with self.assertRaises(ValueError): sdk.check_files(self.root, [self.row])

    def test_size_mismatch_rejected(self):
        with self.assertRaises(ValueError): sdk.check_files(self.root, [dict(self.row, sizeBytes=7)])

    def test_missing_file_rejected(self):
        self.file.unlink()
        with self.assertRaises(ValueError): sdk.check_files(self.root, [self.row])

    def test_path_traversal_rejected(self):
        with self.assertRaises(ValueError): sdk.check_files(self.root, [dict(self.row, path='../escape')])

    def test_absolute_path_rejected(self):
        with self.assertRaises(ValueError): sdk.check_files(self.root, [dict(self.row, path=str(self.file))])

    def test_symlink_escape_rejected(self):
        (self.root / 'lib/escape').symlink_to('/etc/hosts')
        with self.assertRaises(ValueError): sdk.check_files(self.root, [dict(self.row, path='lib/escape')])

    def test_existing_output_preserved(self):
        with self.assertRaises(ValueError): sdk.fresh_output(self.root)
        self.assertEqual(self.file.read_bytes(), b'baseline')

    def test_cached_dependency_mismatch_rejected(self):
        with self.assertRaises(ValueError): sdk.verify_static(self.root, {'lib/test.so': '0'*64})

    def test_comparison_reports_each_mismatch(self):
        names = {'test.so': self.row['sha256']}
        self.assertTrue(sdk.compare_libraries(self.root, names)['allMatch'])
        self.file.write_bytes(b'different')
        report = sdk.compare_libraries(self.root, names)
        self.assertFalse(report['allMatch'])
        self.assertEqual(report['libraries'][0]['name'], 'test.so')
        self.assertFalse(report['libraries'][0]['matches'])

    def test_manifest_requires_pinned_hash_before_parsing(self):
        (self.root / 'manifest.json').write_text('{}')
        with self.assertRaisesRegex(ValueError, 'manifest SHA256'):
            sdk.verify_manifest(self.root, '0'*64)

    def test_incomplete_manifest_rejected(self):
        (self.root / 'manifest.json').write_text('{}')
        with self.assertRaises(ValueError): sdk.verify_manifest(self.root)

class ManifestContractTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        def put(name, data=b'fixture'):
            p = self.root / name
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_bytes(data)
            return sdk.record(p, self.root)
        libraries = [dict(put('lib/'+name), name=name) for name in sorted(sdk.NAMES)]
        proof = put('evidence/producer-working-tree.patch')
        patches = [put('evidence/patches/'+Path(n).name, (sdk.HERE/n).read_bytes()) for n in sdk.LOCK['patches']]
        header = put('include/libavcodec/ohcodec_buffer.h')
        pc = put('lib/pkgconfig/libavcodec.pc')
        sbom = put('sbom.json', b'{}')
        tool = put('evidence/tools.json', b'{}')
        self.m = {'schemaVersion':1, 'artifactKind':'source-build',
            'producer':{'repository':'https://github.com/yaoshining/ohos_ijkplayer.git','revision':'a'*40,
                        'workingTreePatchSha256':proof['sha256'],'workingTreePatchPath':proof['path']},
            'baseline':{k:sdk.LOCK[k] for k in ('tvCommit','harSha256','mpvSha256')}, 'targetAbi':'arm64-v8a',
            'sources':[{'name':'FFmpeg','revision':sdk.LOCK['ffmpegCommit'],'archiveSha256':'b'*64},
                       {'name':'libmpv-ohos-build','revision':sdk.LOCK['builderCommit']}],
            'patches':patches, 'tools':{'currentBuild':tool['path']},
            'staticDependencies':{'rebuiltFromSource':False,'fullyVerified':False},
            'libraries':libraries,'headers':{'status':'ready','files':[header]},'pkgconfig':{'status':'ready','files':[pc]},
            'licenses':[],'sbom':sbom,'rebuildComparison':sdk.compare_libraries(self.root,sdk.LOCK['libraries']),
            'deviceAcceptanceStatus':'pending',
            'files':[sdk.record(p,self.root) for p in self.root.rglob('*') if p.is_file()]}

    def verify(self):
        sdk.write_json(self.root/'manifest.json', self.m)
        return sdk.verify_manifest(self.root)

    def test_valid_source_manifest(self):
        self.verify()

    def test_missing_producer_identity_rejected(self):
        self.m['producer'] = {}
        with self.assertRaises(ValueError): self.verify()

    def test_unlocked_source_rejected(self):
        self.m['sources'][0]['revision'] = '0'*40
        with self.assertRaises(ValueError): self.verify()

    def test_patch_reference_tamper_rejected(self):
        self.m['patches'][0]['sha256'] = '0'*64
        with self.assertRaises(ValueError): self.verify()

    def test_empty_ready_headers_rejected(self):
        self.m['headers']['files'] = []
        with self.assertRaises(ValueError): self.verify()

    def test_false_comparison_rejected(self):
        self.m['rebuildComparison']['allMatch'] = True
        with self.assertRaises(ValueError): self.verify()

    def test_source_rebuilt_dependencies_with_pinned_proof(self):
        p=self.root/'evidence/dependency-source-manifest.json';p.write_text('{"fullyVerified":false}')
        row=sdk.record(p,self.root);self.m['files'].append(row)
        self.m['staticDependencies'].update(rebuiltFromSource=True,sourceManifestSha256=row['sha256'],sourceManifestPath=row['path'])
        self.verify()

    def test_fake_dependency_closure_claim_rejected(self):
        self.m['staticDependencies']['fullyVerified'] = True
        with self.assertRaises(ValueError): self.verify()

class StaticManifestTest(unittest.TestCase):
    def setUp(self):
        from argparse import Namespace
        self.t=tempfile.TemporaryDirectory();self.addCleanup(self.t.cleanup);self.root=Path(self.t.name)
        rows=[]
        for name in sdk.LOCK['staticInputs']:
            p=self.root/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b'archive');rows.append(sdk.record(p,self.root))
        h=self.root/'include/libsmbclient.h';h.parent.mkdir();h.write_text('header')
        self.m={'targetAbi':'arm64-v8a','sourceBuildComplete':True,'fullyVerified':False,'archives':rows,'headers':[sdk.record(h,self.root)],'pkgconfig':[]}
        self.path=self.root/'dependency-manifest.json';self.args=Namespace(smb=self.root,static_manifest=self.path,static_manifest_sha256='')
    def setup_manifest(self):
        sdk.write_json(self.path,self.m);self.args.static_manifest_sha256=sdk.sha(self.path)
    def test_valid_static_source_inputs(self):
        self.setup_manifest();self.assertEqual(set(sdk.static_input(self.args)),set(sdk.LOCK['staticInputs']))
    def test_duplicate_archive_rejected(self):
        self.m['archives'].append(self.m['archives'][0]);self.setup_manifest()
        with self.assertRaises(ValueError):sdk.static_input(self.args)
    def test_header_modified_after_source_manifest_rejected(self):
        self.setup_manifest();(self.root/'include/libsmbclient.h').write_text('changed')
        with self.assertRaises(ValueError):sdk.static_input(self.args)

class ElfAuditTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        (self.root / 'lib').mkdir()
        for name in sdk.NAMES:
            (self.root / 'lib' / name).write_bytes(b'h264_ohcodec\0hevc_ohcodec\0libsmbclient https GnuTLS')

    def inspect(self, symbol_library, symbol='av_ohcodec_release_buffer'):
        def output(args, **kwargs):
            if '-h' in args: return b'ELF64 AArch64'
            if '-d' in args: return f'(SONAME) [{Path(args[-1]).name}]'.encode()
            if '--defined-only' in args and Path(args[-1]).name == symbol_library:
                return f'000 T {symbol}@@LIBAVCODEC_62\n'.encode()
            return b''
        with patch.object(sdk, 'run', side_effect=output):
            sdk.audit(self.root, self.root)

    def test_release_export_in_codec_accepted(self):
        self.inspect('libavcodec.so.62')

    def test_release_export_in_util_accepted(self):
        self.inspect('libavutil.so.60')

    def test_similar_export_rejected(self):
        with self.assertRaises(ValueError):
            self.inspect('libavcodec.so.62','av_ohcodec_release_buffer_invalid')

if __name__ == '__main__': unittest.main()
