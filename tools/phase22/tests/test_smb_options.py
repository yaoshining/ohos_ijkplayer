from pathlib import Path
import subprocess,tempfile,unittest
R=Path(__file__).resolve().parents[1]
class SmbOptions(unittest.TestCase):
 def test_credential_separation_and_invalid_url(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d);(p/'t.cpp').write_text('''#include "smb_options.h"
#include <cassert>
int main(){p22_smb_options o;assert(p22_split_smb("smb://test:dummy-safe@192.168.3.199:1445/FIXTURE/seek.bin",o));assert(o.url=="smb://192.168.3.199:1445/FIXTURE/seek.bin"&&o.user=="test"&&o.password=="dummy-safe");assert(!p22_split_smb("smb://host/file",o));assert(!p22_split_smb("smb://u:p@host/file\\n",o));assert(!p22_split_smb("http://u:p@host/file",o));}''')
   subprocess.run(['c++','-std=c++17','-I'+str(R),str(p/'t.cpp'),'-o',str(p/'t')],check=True);subprocess.run([str(p/'t')],check=True)
