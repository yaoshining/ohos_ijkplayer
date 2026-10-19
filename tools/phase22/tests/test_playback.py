import pathlib,subprocess,tempfile,unittest,sys
ROOT=pathlib.Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
class Playback(unittest.TestCase):
 def test_surface_policy(self):
  with tempfile.TemporaryDirectory() as tmp:
   p=pathlib.Path(tmp);(p/'main.c').write_text('''#include <assert.h>
int p22_surface_valid(const char*,int,int);
int main(){assert(p22_surface_valid("123456789012345",640,360));assert(!p22_surface_valid("0",640,360));assert(!p22_surface_valid("-1",640,360));assert(!p22_surface_valid("123x",640,360));assert(!p22_surface_valid("18446744073709551616",640,360));assert(!p22_surface_valid("1",0,360));assert(!p22_surface_valid(0,640,360));}
''');subprocess.run(['cc',str(p/'main.c'),str(ROOT/'play_policy.c'),'-o',str(p/'test')],check=True);subprocess.run([str(p/'test')],check=True)
 def test_acceptance_rejects_fallback_and_no_frames(self):
  from acceptance import accept_playback
  valid=dict(loaded=True,eof=True,frames=360,hwdec='ohcodec',ao='ohaudio',gpu='ohos',maxDrift=.02,driftSamples=20,seekConfirmed=True)
  self.assertTrue(accept_playback(valid,'ohos',True)['passed'])
  for key,value in [('seekConfirmed',False),('loaded',False),('eof',False),('frames',0),('hwdec','no'),('ao','null'),('gpu',''),('maxDrift',None),('maxDrift',float('nan')),('maxDrift',float('inf')),('maxDrift','0.01'),('driftSamples',0),('driftSamples',None)]:
   x=valid.copy();x[key]=value;self.assertFalse(accept_playback(x,'ohos',True)['passed'],key)
