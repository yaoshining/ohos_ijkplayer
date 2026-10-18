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
    def test_recipe_and_default_workflow_unchanged(self):
        r=Path(__file__).resolve().parents[3];base=r/'tools/ffmpeg8';workflow=r/'.github/workflows/build-ffmpeg8.yml'
        before=hp.pins([workflow,*[base/n for n in hp.RECIPE]])
        with tempfile.TemporaryDirectory() as tmp:runner.recipe(base,Path(tmp)/'recipe','hx509-history')
        self.assertEqual(before,hp.pins([workflow,*[base/n for n in hp.RECIPE]]))
if __name__=='__main__':unittest.main()
