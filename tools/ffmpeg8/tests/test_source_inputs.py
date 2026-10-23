"""下载输入在解压前必须被来源锁绑定；缓存也不能免验。"""
import importlib.util
import hashlib
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import sys
sys.dont_write_bytecode=True
p=Path(__file__).parents[1]/'fetch-sources.py'
spec=importlib.util.spec_from_file_location('sources',p);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
class SourceInputTest(unittest.TestCase):
    def setUp(self):
        self.t=tempfile.TemporaryDirectory();self.addCleanup(self.t.cleanup);self.p=Path(self.t.name)/'archive.tar.gz';self.p.write_bytes(b'source')
        self.good=hashlib.sha256(b'source').hexdigest()
    def test_valid_digest(self): m.verify(self.p,self.good)
    def test_corrupt_cached_archive_rejected(self):
        self.p.write_bytes(b'SOURCE')
        with self.assertRaises(ValueError):m.verify(self.p,self.good)
    def test_missing_digest_rejected(self):
        with self.assertRaises(ValueError):m.verify(self.p,'')
    def test_non_sha256_rejected(self):
        with self.assertRaises(ValueError):m.verify(self.p,'version-1.0')
    def test_missing_archive_rejected(self):
        self.p.unlink()
        with self.assertRaises(ValueError):m.verify(self.p,self.good)
    def test_unlocked_source_name_rejected(self):
        with self.assertRaises(ValueError):m.select({'sources':[]},'unlocked')
class FetchTest(unittest.TestCase):
    def setUp(self):
        self.t=tempfile.TemporaryDirectory();self.addCleanup(self.t.cleanup);self.root=Path(self.t.name)
        self.row={'name':'fixture','kind':'release-archive','archiveFile':'source.tar.gz','url':'https://example.invalid/source.tar.gz','sha256':hashlib.sha256(b'source').hexdigest()}
    def test_offline_release_cannot_bypass_with_git_repo(self):
        with patch.object(m.subprocess,'run') as run:
            with self.assertRaises(ValueError):m.fetch(self.row,self.root,git_repo=self.root,offline=True)
            run.assert_not_called()
    def test_verified_cache_never_downloads(self):
        (self.root/'source.tar.gz').write_bytes(b'source')
        with patch.object(m.subprocess,'run') as run:
            self.assertEqual(m.fetch(self.row,self.root,offline=True),self.root/'source.tar.gz')
            run.assert_not_called()
    def test_corrupt_cache_rejected_without_network(self):
        (self.root/'source.tar.gz').write_bytes(b'corrupt')
        with patch.object(m.subprocess,'run') as run:
            with self.assertRaises(ValueError):m.fetch(self.row,self.root)
            run.assert_not_called()
    def test_corrupt_download_not_promoted(self):
        def download(args,**kwargs):(self.root/'source.tar.gz.partial').write_bytes(b'corrupt')
        with patch.object(m.subprocess,'run',side_effect=download):
            with self.assertRaises(ValueError):m.fetch(self.row,self.root)
        self.assertFalse((self.root/'source.tar.gz').exists())
        self.assertFalse((self.root/'source.tar.gz.partial').exists())
if __name__=='__main__':unittest.main()
