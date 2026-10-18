import hashlib,io,json,sys,tarfile,tempfile,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'runtime'))
from input_gate import inventory,verify_tree,require_fresh,safe_extract,source_version
class InputGate(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name)
 def test_exact_source(self):
  (self.root/'a.c').write_text('int a;');verify_tree(self.root,inventory(self.root),source=True)
 def test_mutation(self):
  p=self.root/'a.c';p.write_text('int a;');rows=inventory(self.root);p.write_text('int b;')
  with self.assertRaises(ValueError):verify_tree(self.root,rows)
 def test_extra(self):
  rows=inventory(self.root);(self.root/'extra').touch()
  with self.assertRaises(ValueError):verify_tree(self.root,rows)
 def test_missing(self):
  p=self.root/'a';p.touch();rows=inventory(self.root);p.unlink()
  with self.assertRaises(ValueError):verify_tree(self.root,rows)
 def test_target_object(self):
  (self.root/'bad.o').touch()
  with self.assertRaises(ValueError):verify_tree(self.root,inventory(self.root),source=True)
 def test_python_cache(self):
  (self.root/'__pycache__').mkdir();(self.root/'__pycache__/a.pyc').touch()
  with self.assertRaises(ValueError):verify_tree(self.root,inventory(self.root),source=True)
 def test_fresh(self):self.assertEqual(require_fresh(self.root/'new'),self.root/'new')
 def test_existing_empty(self):
  with self.assertRaises(ValueError):require_fresh(self.root)
 def test_dangling_symlink(self):
  p=self.root/'link';p.symlink_to('absent')
  with self.assertRaises(ValueError):require_fresh(p)
 def test_unlisted_dangling_source_link(self):
  rows=inventory(self.root);(self.root/'dangling').symlink_to('absent')
  with self.assertRaises(ValueError):verify_tree(self.root,rows,source=True)
 def test_unlisted_directory_link(self):
  (self.root/'directory').mkdir();rows=inventory(self.root);(self.root/'dirlink').symlink_to('directory',target_is_directory=True)
  with self.assertRaises(ValueError):verify_tree(self.root,rows,source=True)
 def test_link_changed_to_regular_file(self):
  (self.root/'a').write_text('abc');p=self.root/'b';p.symlink_to('a');rows=inventory(self.root);p.unlink();p.write_text('abc')
  with self.assertRaises(ValueError):verify_tree(self.root,rows,source=True)
 def test_empty_build_directory(self):
  rows=inventory(self.root);(self.root/'target').mkdir()
  with self.assertRaises(ValueError):verify_tree(self.root,rows,source=True)
 def archive(self,name,link=None):
  p=self.root/'input.tar'
  with tarfile.open(p,'w') as t:
   i=tarfile.TarInfo(name)
   if link:i.type=tarfile.SYMTYPE;i.linkname=link
   else:i.size=3
   t.addfile(i,None if link else io.BytesIO(b'abc'))
  return p
 def test_archive_normal(self):
  safe_extract(self.archive('a.c'),self.root/'export');self.assertEqual((self.root/'export/a.c').read_text(),'abc')
 def test_archive_traversal(self):
  with self.assertRaises(ValueError):safe_extract(self.archive('../outside'),self.root/'export')
 def test_archive_external_link(self):
  with self.assertRaises(ValueError):safe_extract(self.archive('bad','/etc/passwd'),self.root/'export')
 def test_version_strict(self):
  p=self.root/'.phase18-source-version';p.write_text('1'*40+'\n');self.assertEqual(source_version(self.root),'1'*40)
  p.write_text('parent-head')
  with self.assertRaises(ValueError):source_version(self.root)
 def test_version_missing_no_fallback(self):
  with self.assertRaises(ValueError):source_version(self.root)
if __name__=='__main__':unittest.main()
