from pathlib import Path
import json,tempfile,unittest,sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from compile_inputs import parse_ninja_deps,collect_compile_inputs,compare_compile_inputs
BASE=Path(__file__).resolve().parent
class CompileInputsTests(unittest.TestCase):
 def fixture(self,base):
  root=base/'run';sdk=base/'sdk';sdk.mkdir(parents=True);(sdk/'stdio.h').write_text('sdk')
  for stage in ['mpv','libplacebo']:
   build=root/stage/'build';build.mkdir(parents=True);source=root/stage/'source';source.mkdir();(source/'x.c').write_text('source');(build/'config.h').write_text('generated')
   (build/'compile_commands.json').write_text(json.dumps([{'directory':str(build),'file':'../source/x.c','output':'x.o'}]))
   (root/'logs').mkdir(exist_ok=True);(root/'logs'/(stage+'-deps.log')).write_text('x.o: #deps 3, deps mtime 123 (VALID)\n    ../source/x.c\n    config.h\n    '+str(sdk/'stdio.h')+'\n\n')
  return root,sdk
 def test_parse_valid(self):self.assertEqual(parse_ninja_deps('a.o: #deps 1, deps mtime 0 (VALID)\n    a.c\n'),{'a.o':['a.c']})
 def test_repeated_dependency_entries_preserve_actual_count(self):
  self.assertEqual(parse_ninja_deps('a.o: #deps 2, deps mtime 0 (VALID)\n    a.h\n    a.h\n'),{'a.o':['a.h','a.h']})
 def test_parse_rejects_bad_count_duplicate_stale(self):
  for text in ['','a.o: #deps 2, deps mtime 0 (VALID)\n    a.c\n','a.o: #deps 1, deps mtime 0 (STALE)\n    a.c\n','a.o: #deps 1, deps mtime 0 (VALID)\n    a.c\na.o: #deps 1, deps mtime 0 (VALID)\n    a.c\n']:
   with self.subTest(text=text),self.assertRaises(ValueError):parse_ninja_deps(text)
 def test_normal_cross_root_and_generated_header(self):
  with tempfile.TemporaryDirectory(dir=BASE) as tmp:
   a,sa=self.fixture(Path(tmp)/'a');b,sb=self.fixture(Path(tmp)/'long/b');x=collect_compile_inputs(a,sa);y=collect_compile_inputs(b,sb)
   self.assertTrue(compare_compile_inputs(x,y)['passed']);self.assertEqual(x['counts']['objects'],2);self.assertEqual(x['counts']['sources'],2);self.assertEqual(x['counts']['includedFiles'],3);self.assertEqual(x['counts']['generatedFiles'],2)
 def test_changed_header_rejected(self):
  with tempfile.TemporaryDirectory(dir=BASE) as tmp:
   a,sa=self.fixture(Path(tmp)/'a');b,sb=self.fixture(Path(tmp)/'b');(b/'mpv/build/config.h').write_text('different')
   self.assertFalse(compare_compile_inputs(collect_compile_inputs(a,sa),collect_compile_inputs(b,sb))['passed'])
 def test_missing_object_coverage_rejected(self):
  with tempfile.TemporaryDirectory(dir=BASE) as tmp:
   a,sa=self.fixture(Path(tmp));(a/'mpv/build/compile_commands.json').write_text('[]')
   with self.assertRaises(ValueError):collect_compile_inputs(a,sa)
 def test_missing_and_outside_file_rejected(self):
  with tempfile.TemporaryDirectory(dir=BASE) as tmp:
   a,sa=self.fixture(Path(tmp));p=a/'logs/mpv-deps.log';original=p.read_text()
   for path in [str(Path(tmp)/'outside.h'),str(a/'missing.h')]:
    p.write_text(original.replace(str(sa/'stdio.h'),path))
    with self.subTest(path=path),self.assertRaises((ValueError,FileNotFoundError)):collect_compile_inputs(a,sa)
 def test_same_root_or_missing_evidence_rejected(self):
  with tempfile.TemporaryDirectory(dir=BASE) as tmp:
   a,sa=self.fixture(Path(tmp));row=collect_compile_inputs(a,sa)
   with self.assertRaises(ValueError):compare_compile_inputs(row,row)
   with self.assertRaises(ValueError):compare_compile_inputs(row,{})
if __name__=='__main__':unittest.main()
