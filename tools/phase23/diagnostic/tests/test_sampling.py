from pathlib import Path
import subprocess,tempfile,unittest
R=Path(__file__).resolve().parents[1]
class Sampling(unittest.TestCase):
 def test_real_frame_required_and_supported_time_property(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d);(p/'mpv').mkdir();(p/'mpv/client.h').write_text('typedef struct mpv_handle mpv_handle;enum {MPV_FORMAT_FLAG=3,MPV_FORMAT_DOUBLE=5};extern "C" int mpv_get_property(mpv_handle*,const char*,int,void*);')
   (p/'test.cpp').write_text('''#include <cstring>
#include <cassert>
#include <mpv/client.h>
+extern int p22_sample_video(mpv_handle*,double*);static bool frame=true;
+extern "C" int mpv_get_property(mpv_handle*,const char*n,int,void*v){if(!strcmp(n,"video-frame-info/interlaced"))return frame?0:-10;if(!strcmp(n,"time-pos")){*(double*)v=5.0;return 0;}return -8;}
+int main(){double p=0;assert(p22_sample_video(nullptr,&p)==0&&p==5.0);frame=false;assert(p22_sample_video(nullptr,&p)<0);}
+'''.replace('\n+','\n'));subprocess.run(['c++','-I'+str(p),str(p/'test.cpp'),str(R/'sampling.cpp'),'-o',str(p/'test')],check=True);subprocess.run([str(p/'test')],check=True)
