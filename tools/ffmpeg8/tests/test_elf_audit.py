import importlib.util
from pathlib import Path
import struct
import unittest

spec=importlib.util.spec_from_file_location('elf_audit',Path(__file__).resolve().parents[1]/'elf-audit.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)

def fixture(text=b'\xc0\x03\x5f\xd6',debug=b'path-A'):
    names=b'\0.shstrtab\0.text\0.debug_info\0.bss\0'
    chunks=[b'',names,text,debug,b'']
    data=bytearray(64);headers=[bytes(64)]
    for name,typ,flags,chunk in [(1,3,0,names),(11,1,6,text),(17,1,0,debug),(29,8,3,b'')]:
        off=len(data);data.extend(chunk)
        headers.append(struct.pack('<IIQQQQIIQQ',name,typ,flags,0,off,16 if typ==8 else len(chunk),0,0,1,0))
    shoff=len(data);data.extend(b''.join(headers))
    data[:64]=struct.pack('<16sHHIQQQIHHHHHH',b'\x7fELF\x02\x01\x01'+bytes(9),3,183,1,0,0,shoff,0,64,0,0,64,5,1)
    return bytes(data)

class ElfAuditTests(unittest.TestCase):
    def test_debug_change_does_not_claim_code_change(self):
        a=m.inventory(fixture());b=m.inventory(fixture(debug=b'path-B'))
        c=m.compare(a,b)
        self.assertEqual(c['changedAllocatedSections'],[])
        self.assertEqual(c['changedSections'],['.debug_info'])
        self.assertFalse(c['behaviorEquivalenceProven'])
    def test_real_code_change_not_hidden_as_debug(self):
        c=m.compare(m.inventory(fixture()),m.inventory(fixture(text=b'ABCD')))
        self.assertEqual(c['changedAllocatedSections'],['.text'])
    def test_bss_is_not_read_from_file(self):
        a=m.inventory(fixture());self.assertIsNone(a['sections']['.bss']['sha256'])
        self.assertEqual(a['sections']['.bss']['size'],16)
    def test_truncated_and_wrong_arch_rejected(self):
        for data in [b'bad',fixture()[:-1],fixture()[:18]+b'\x3e\0'+fixture()[20:]]:
            with self.assertRaises(ValueError):m.inventory(data)

if __name__=='__main__':unittest.main()
