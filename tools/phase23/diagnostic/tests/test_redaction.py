from pathlib import Path
import subprocess,tempfile,unittest
R=Path(__file__).resolve().parents[1]
class Redaction(unittest.TestCase):
 def test_password_and_url_never_returned(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d);(p/'test.cpp').write_text('''#include "safe_log.h"
#include <cassert>
+int main(){auto r=p22_redact("failed smb://user:secret@host/share secret",{"secret"});assert(r.find("secret")==std::string::npos);assert(r.find("host/share")==std::string::npos);assert(r.find("failed")!=std::string::npos);}
+'''.replace('\n+','\n'));subprocess.run(['c++','-std=c++17','-I'+str(R),str(p/'test.cpp'),'-o',str(p/'test')],check=True);subprocess.run([str(p/'test')],check=True)
