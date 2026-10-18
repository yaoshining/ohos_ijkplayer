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

    def test_flex_compatibility_is_linux_only_and_does_not_change_parent_env(self):
        from unittest.mock import patch
        env={'CFLAGS':'-O2'}
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);lib=root/'libbsd.so.0';lib.write_bytes(b'library')
            header=root/'linux-flex-compat.h';header.write_bytes(b'header')
            with patch('run.platform.system',return_value='Linux'):
                selected,pins=runner.flex_environment(env,root,lib)
            self.assertEqual(selected['LIBS'],str(lib.resolve()))
            self.assertIn(str(header),selected['CPPFLAGS'])
            self.assertEqual(len(pins),2);self.assertEqual(env,{'CFLAGS':'-O2'})
            with patch('run.platform.system',return_value='Darwin'):
                selected,pins=runner.flex_environment(env,root,lib)
            self.assertEqual(selected,env);self.assertEqual(pins,[])

    def test_linux_compatibility_rejects_missing_library_or_header(self):
        from unittest.mock import patch
        with tempfile.TemporaryDirectory() as tmp, patch('run.platform.system',return_value='Linux'):
            root=Path(tmp);lib=root/'libbsd.so.0'
            with self.assertRaises(ValueError):runner.flex_environment({},root,lib)
            lib.write_bytes(b'library')
            with self.assertRaises(ValueError):runner.flex_environment({},root,lib)

    def test_fixed_flex_source_patch_and_double_application_rejection(self):
        import shutil
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);source=root/'source';(source/'src').mkdir(parents=True)
            shutil.copy2(Path(__file__).parent/'fixtures/apple-flex35-main.c',source/'src/main.c')
            skel=source/'src/skel.c';skel.write_bytes(b'unchanged skeleton')
            pins=runner.patch_linux_flex(source,root)
            runner.verify_extra(pins)
            self.assertEqual(skel.read_bytes(),b'unchanged skeleton')
            self.assertNotEqual(hp.sha(source/'src/main.c'),hp.sha(Path(__file__).parent/'fixtures/apple-flex35-main.c'))
            self.assertTrue((root/'linux-flex-main.patch').is_file())
            with self.assertRaises(ValueError):runner.patch_linux_flex(source,root)
            skel.write_bytes(b'drift')
            with self.assertRaises(ValueError):runner.verify_extra(pins)
    def test_drifted_flex_source_is_rejected_before_patch(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);(root/'src').mkdir();p=root/'src/main.c';p.write_text('unknown source')
            with self.assertRaises(ValueError):runner.patch_linux_flex(root,root)
            self.assertEqual(p.read_text(),'unknown source');self.assertFalse((root/'linux-flex-main.patch').exists())

    def test_recipe_and_default_workflow_unchanged(self):
        r=Path(__file__).resolve().parents[3];base=r/'tools/ffmpeg8';workflow=r/'.github/workflows/build-ffmpeg8.yml'
        before=hp.pins([workflow,*[base/n for n in hp.RECIPE]])
        with tempfile.TemporaryDirectory() as tmp:
            dest=Path(tmp)/'recipe';runner.recipe(base,dest,'hx509-history')
            self.assertEqual((dest/'linux-flex-compat.h').read_bytes(),(base.parent/'hx509-history/linux-flex-compat.h').read_bytes())
        self.assertEqual(before,hp.pins([workflow,*[base/n for n in hp.RECIPE]]))
if __name__=='__main__':unittest.main()
