from pathlib import Path
import tempfile,tarfile,io,sys,unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from extract import extract_source
class Extraction(unittest.TestCase):
 def archive(self,base,child=False):
  a=base/'source.tar'
  with tarfile.open(a,'w') as t:
   m=tarfile.TarInfo('src/link');m.type=tarfile.SYMTYPE;m.linkname='../../outside';t.addfile(m)
   if child:
    m=tarfile.TarInfo('src/link/write');m.size=1;t.addfile(m,io.BytesIO(b'x'))
  return a
 def test_external_link_is_metadata_not_write(self):
  with tempfile.TemporaryDirectory() as d:
   b=Path(d);r=extract_source(self.archive(b),b/'new',True)
   self.assertEqual(len(r['externalRelativeSymlinks']),1);self.assertTrue((b/'new/src/link').is_symlink());self.assertFalse((b/'outside').exists())
 def test_never_write_through_archive_link(self):
  with tempfile.TemporaryDirectory() as d:
   b=Path(d)
   with self.assertRaises(ValueError):extract_source(self.archive(b,True),b/'new',True)
   self.assertFalse((b/'outside').exists())
