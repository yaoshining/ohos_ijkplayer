import pathlib,subprocess,tempfile,unittest
ROOT=pathlib.Path(__file__).resolve().parents[1]
class Modes(unittest.TestCase):
 def test_target_mode_contract(self):
  with tempfile.TemporaryDirectory() as tmp:
   p=pathlib.Path(tmp);(p/'test.c').write_text('''#include <assert.h>
int p22_mode(const char*);
int main(void){assert(p22_mode("init")==1);assert(p22_mode("repeat")==2);assert(p22_mode("conflict")==3);assert(p22_mode("late")==0);assert(p22_mode("cache-write")==0);assert(p22_mode("cache-denied")==0);assert(p22_mode("render")==0);assert(p22_mode("unknown")==0);assert(p22_mode(0)==0);return 0;}
''');subprocess.run(['cc',str(p/'test.c'),str(ROOT/'modes.c'),'-o',str(p/'test')],check=True);subprocess.run([str(p/'test')],check=True)
