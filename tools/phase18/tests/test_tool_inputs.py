from pathlib import Path
import sys,tempfile,unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from tool_inputs import python_inputs
class PythonTools(unittest.TestCase):
 def test_stdlib_bytecode_is_bound(self):
  with tempfile.TemporaryDirectory() as t:
   r=Path(t);(r/'__pycache__').mkdir();(r/'a.py').write_text('x');(r/'__pycache__/a.pyc').write_bytes(b'compiled')
   self.assertEqual({p.relative_to(r).as_posix() for p,role in python_inputs(r,{})},{'a.py','__pycache__/a.pyc'})
 def test_ambient_packages_excluded_but_selected_modules_bound(self):
  with tempfile.TemporaryDirectory() as t:
   r=Path(t);(r/'site-packages/selected/__pycache__').mkdir(parents=True);(r/'site-packages/ambient.py').touch();(r/'site-packages/selected/__pycache__/a.pyc').touch()
   rows=list(python_inputs(r,{'selected':r/'site-packages/selected'}));self.assertEqual(len(rows),1);self.assertEqual(rows[0][1],'Python module selected')
