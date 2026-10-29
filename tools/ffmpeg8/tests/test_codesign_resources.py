import importlib.util
from pathlib import Path
import struct,hashlib,unittest,plistlib,tempfile
spec=importlib.util.spec_from_file_location('seal',Path(__file__).resolve().parents[1]/'codesign-resources.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
def fixture(resource=b'abc'):
    cd=bytearray(44+96);struct.pack_into('>9I4B I',cd,0,0xfade0c02,len(cd),0x20001,0,len(cd),0,3,0,0,32,2,0,12,0);cd[44:76]=hashlib.sha256(resource).digest()
    blob=struct.pack('>5I',0xfade0cc0,20+len(cd),1,0,20)+cd
    mach=struct.pack('<8I',0xfeedfacf,0x100000c,0,2,1,16,0,0)+struct.pack('<4I',0x1d,16,48,len(blob))+blob
    return mach
class SealTests(unittest.TestCase):
    def test_signed_slot_matches(self):self.assertTrue(m.resource_binding(fixture(),b'abc')[0]['matches'])
    def test_changed_resources_rejected(self):
        with self.assertRaises(ValueError):m.resource_binding(fixture(),b'changed')
    def test_truncated_signature_rejected(self):
        with self.assertRaises(ValueError):m.resource_binding(fixture()[:-2],b'abc')
    def test_missing_signature_rejected(self):
        with self.assertRaises(ValueError):m.resource_binding(bytes(50),b'abc')
    def test_subtree_rejects_changed_and_extra_files(self):
        with tempfile.TemporaryDirectory() as t:
            root=Path(t);(root/'native').mkdir();(root/'native/a').write_bytes(b'abc')
            seal=plistlib.dumps({'files2':{'native/a':{'hash2':hashlib.sha256(b'abc').digest()}}})
            self.assertEqual(m.subtree_inventory(root,seal,'native')['mismatches'],[])
            (root/'native/a').write_bytes(b'changed');(root/'native/extra').write_bytes(b'extra')
            inv=m.subtree_inventory(root,seal,'native');self.assertEqual(inv['mismatches'],['native/a']);self.assertEqual(inv['extra'],['native/extra'])
    def test_subtree_missing_and_changed_symlink(self):
        with tempfile.TemporaryDirectory() as t:
            root=Path(t);(root/'native').mkdir();(root/'native/link').symlink_to('wrong')
            seal=plistlib.dumps({'files2':{'native/link':{'symlink':'right'},'native/missing':{'hash2':bytes(32)}}})
            inv=m.subtree_inventory(root,seal,'native');self.assertIn('native/link',inv['mismatches']);self.assertEqual(inv['missing'],['native/missing'])
if __name__=='__main__':unittest.main()
