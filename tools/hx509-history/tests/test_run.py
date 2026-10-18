import importlib.util, json, sys, tempfile, unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import run as runner
import profile as hp

class RunnerTests(unittest.TestCase):
    def test_requires_new_root_and_profile(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)/'run'
            for value in [None,'default']:
                with self.assertRaises(ValueError):runner.prepare(root,value)
            self.assertFalse(root.exists())
            runner.prepare(root,'hx509-history')
            with self.assertRaises(ValueError):runner.prepare(root,'hx509-history')
    def test_archive_pin_checked_before_extract(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);archive=root/'source.tar.gz';archive.write_bytes(b'wrong')
            with self.assertRaises(ValueError):runner.extract(archive,root/'source','0'*64)
            self.assertFalse((root/'source').exists())
    def test_native_install_and_cxx_are_explicit_locked_commands(self):
        from unittest.mock import patch
        with patch('run.shutil.which',side_effect=lambda name:'/locked/'+name), patch('run.platform.system',return_value='Linux'):
            env=runner.native_environment(Path('/new/home'))
        self.assertEqual(env['INSTALL'],'/locked/install')
        self.assertEqual(env['CXX'],'/locked/c++')
        self.assertEqual(env['CC'],'/locked/clang')
        self.assertEqual(env['M4'],'/locked/m4')

    def test_extract_works_with_fixed_ci_python_without_filter_keyword(self):
        import io, tarfile
        from unittest.mock import patch
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);archive=root/'source.tar'
            with tarfile.open(archive,'w') as tar:
                info=tarfile.TarInfo('source/file');info.size=3;tar.addfile(info,io.BytesIO(b'abc'))
            original=tarfile.TarFile.extractall
            def old_api(tar,path,**kwargs):
                if 'filter' in kwargs:raise TypeError('unexpected filter keyword')
                return original(tar,path)
            with patch.object(tarfile.TarFile,'extractall',old_api):
                result=runner.extract(archive,root/'output',hp.sha(archive))
            self.assertEqual((result/'file').read_bytes(),b'abc')

    def test_pair_mismatch_requires_actual_fixed_root_control(self):
        from unittest.mock import Mock
        compare=Mock(side_effect=[{'allMatch':False},{'allMatch':True}]);build=Mock(return_value='fixed')
        with tempfile.TemporaryDirectory() as tmp:
            report=runner.compare_chains('a','b',Path(tmp),compare,build)
        build.assert_called_once_with()
        self.assertEqual(compare.call_args_list[1].args,('a','fixed'))
        self.assertFalse(report['pairedAllMatch']);self.assertTrue(report['fixedRootAllMatch'])
    def test_fixed_root_mismatch_is_not_promoted(self):
        from unittest.mock import Mock
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(ValueError):runner.compare_chains('a','b',Path(tmp),Mock(return_value={'allMatch':False}),Mock(return_value='fixed'))

    def test_recipe_and_default_workflow_unchanged(self):
        r=Path(__file__).resolve().parents[3];base=r/'tools/ffmpeg8';workflow=r/'.github/workflows/build-ffmpeg8.yml'
        before=hp.pins([workflow,*[base/n for n in hp.RECIPE]])
        with tempfile.TemporaryDirectory() as tmp:runner.recipe(base,Path(tmp)/'recipe','hx509-history')
        self.assertEqual(before,hp.pins([workflow,*[base/n for n in hp.RECIPE]]))
if __name__=='__main__':unittest.main()
