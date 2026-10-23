from pathlib import Path
import subprocess,tempfile,unittest
R=Path(__file__).resolve().parents[1]
class ResourceCase(unittest.TestCase):
 def test_mutation_is_restored_after_validation(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d);(p/'resources/fonts').mkdir(parents=True);(p/'resources/fonts/font1.ttf').write_bytes(b'fixture');(p/'cache').mkdir()
   (p/'t.cpp').write_text('''#include "resource_case.h"
#include <cassert>
#include <fstream>
int main(int,char**v){std::string root=v[1],font=root+"/resources/fonts/font1.ttf";for(auto mode:{"missing-font","bad-font","font-permission","cache-permission","font-symlink"}){int calls=0;bool ok=p22_resource_case(root,mode,[&](){calls++;return std::string(mode)=="missing-font"?ENOENT:std::string(mode).find("permission")!=std::string::npos?EACCES:EINVAL;},[](auto){});assert(ok&&calls==1);std::ifstream f(font);std::string x;f>>x;assert(x=="fixture");struct stat s;assert(lstat(font.c_str(),&s)==0&&!S_ISLNK(s.st_mode)&&(s.st_mode&0400));}assert(!p22_resource_case(root,"unknown",[]{return 0;},[](auto){}));}''')
   subprocess.run(['c++','-std=c++17','-I'+str(R),str(p/'t.cpp'),'-o',str(p/'t')],check=True);subprocess.run([str(p/'t'),str(p)],check=True)
