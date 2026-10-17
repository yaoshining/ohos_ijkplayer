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
