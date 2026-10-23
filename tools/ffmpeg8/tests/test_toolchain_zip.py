import importlib.util,stat,subprocess,tempfile,unittest,zipfile
from pathlib import Path
class NativeZip(unittest.TestCase):
    def module(self):
        s=importlib.util.spec_from_file_location('ci',Path(__file__).parents[1]/'ci-prepare-inputs.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
    def test_symlink_and_executable_modes_preserved(self):
        with tempfile.TemporaryDirectory() as t:
            root=Path(t);archive=root/'native.zip'
            with zipfile.ZipFile(archive,'w') as z:
                f=zipfile.ZipInfo('native/bin/clang-15');f.external_attr=(stat.S_IFREG|0o755)<<16;z.writestr(f,'#!/bin/sh\nexit 0\n')
                link=zipfile.ZipInfo('native/bin/clang');link.external_attr=(stat.S_IFLNK|0o777)<<16;z.writestr(link,'clang-15')
            self.module().extract_native_zip(archive,root/'out')
            self.assertTrue((root/'out/native/bin/clang').is_symlink())
            subprocess.run([str(root/'out/native/bin/clang')],check=True)
    def test_escape_link_rejected_before_extract(self):
        with tempfile.TemporaryDirectory() as t:
            root=Path(t);archive=root/'native.zip'
            with zipfile.ZipFile(archive,'w') as z:
                f=zipfile.ZipInfo('link');f.external_attr=(stat.S_IFLNK|0o777)<<16;z.writestr(f,'../outside')
            with self.assertRaises(ValueError):self.module().extract_native_zip(archive,root/'out')
    def test_link_parent_cannot_redirect_member(self):
        with tempfile.TemporaryDirectory() as t:
            root=Path(t);archive=root/'native.zip'
            with zipfile.ZipFile(archive,'w') as z:
                f=zipfile.ZipInfo('link');f.external_attr=(stat.S_IFLNK|0o777)<<16;z.writestr(f,'inside');z.writestr('link/file','data')
            with self.assertRaises(ValueError):self.module().extract_native_zip(archive,root/'out')
if __name__=='__main__':unittest.main()
