import importlib.util,tempfile,unittest
from pathlib import Path
class GeneratorLock(unittest.TestCase):
    def test_generated_tool_cannot_change_after_stamp(self):
        spec=importlib.util.spec_from_file_location('g',Path(__file__).parents[1]/'generator-lock.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
        with tempfile.TemporaryDirectory() as t:
            root=Path(t);f=root/'tool';f.write_bytes(b'generated');row=m.stamp([f],'a'*64)
            m.verify(row);f.write_bytes(b'changed')
            with self.assertRaises(ValueError):m.verify(row)
if __name__=='__main__':unittest.main()

class GeneratorResources(unittest.TestCase):
    def test_added_resource_after_cli_stamp_is_rejected(self):
        import subprocess,json,sys
        spec=importlib.util.spec_from_file_location('g',Path(__file__).parents[1]/'generator-lock.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
        with tempfile.TemporaryDirectory() as t:
            root=Path(t);tool=root/'bison';tool.write_text('tool');resources=root/'share';resources.mkdir();(resources/'yacc.c').write_text('skeleton');out=root/'lock.json'
            subprocess.run([sys.executable,str(Path(__file__).parents[1]/'generator-lock.py'),'--output',str(out),'--host-lock-sha256','a'*64,'--directory',str(resources),str(tool)],check=True)
            row=json.loads(out.read_text());m.verify(row);(resources/'new.m4').write_text('new')
            with self.assertRaises(ValueError):m.verify(row)

class GeneratorSymlinkBoundary(unittest.TestCase):
    def test_resource_symlink_cannot_escape_frozen_inventory(self):
        import subprocess,sys
        with tempfile.TemporaryDirectory() as t:
            root=Path(t);tool=root/'bison';tool.write_text('tool');resources=root/'share';resources.mkdir();outside=root/'outside';outside.write_text('skeleton');(resources/'yacc.c').symlink_to(outside)
            result=subprocess.run([sys.executable,str(Path(__file__).parents[1]/'generator-lock.py'),'--output',str(root/'lock.json'),'--host-lock-sha256','a'*64,'--directory',str(resources),str(tool)],capture_output=True)
            self.assertNotEqual(result.returncode,0)
