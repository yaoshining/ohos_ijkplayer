"""宿主工具与目标库来源不能混为一谈。"""
from pathlib import Path
import hashlib,importlib.util,tempfile,unittest,sys
sys.dont_write_bytecode=True
spec=importlib.util.spec_from_file_location('deps',Path(__file__).parents[1]/'dependency-manifest.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
class DependencyManifestTest(unittest.TestCase):
    def setUp(self):
        self.t=tempfile.TemporaryDirectory();self.addCleanup(self.t.cleanup);self.root=Path(self.t.name);self.cache=self.root/'cache';self.cache.mkdir();self.sdk=self.root/'sdk';self.sdk.mkdir()
        self.row={'name':'bison-3.8.2','role':'optional-host-tool','archiveFile':'bison.tar.gz','sha256':hashlib.sha256(b'source').hexdigest()}
    def test_external_modern_bison_does_not_require_unused_archive(self):
        rows=m.source_records({'sources':[self.row]},self.cache,self.sdk)
        self.assertEqual(rows[0]['useStatus'],'not-used-external-host-tool')
    def test_source_built_bison_requires_archive(self):
        (self.sdk/'bin').mkdir();(self.sdk/'bin/bison').write_text('built')
        with self.assertRaises(ValueError):m.source_records({'sources':[self.row]},self.cache,self.sdk)
    def test_target_library_cannot_skip_missing_source(self):
        row=dict(self.row,name='gmp-6.3.0',role='target-library')
        with self.assertRaises(ValueError):m.source_records({'sources':[row]},self.cache,self.sdk)
    def test_downloaded_host_archive_does_not_prove_it_was_built(self):
        (self.cache/'bison.tar.gz').write_bytes(b'source')
        rows=m.source_records({'sources':[self.row]},self.cache,self.sdk)
        self.assertEqual(rows[0]['useStatus'],'not-used-external-host-tool')
if __name__=='__main__':unittest.main()
