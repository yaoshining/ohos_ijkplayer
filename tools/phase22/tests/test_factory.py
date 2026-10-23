from pathlib import Path
import subprocess,tempfile,unittest
R=Path(__file__).resolve().parents[1]
class NativeFactory(unittest.TestCase):
 def test_order_and_all_option_failure_cleanup(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d);(p/'mpv').mkdir();(p/'mpv/client.h').write_text('''#pragma once
typedef struct mpv_handle {int unused;} mpv_handle;
#ifdef __cplusplus
extern "C" {
#endif
mpv_handle *mpv_create(void);int mpv_set_option_string(mpv_handle*,const char*,const char*);int mpv_initialize(mpv_handle*);void mpv_terminate_destroy(mpv_handle*);
#ifdef __cplusplus
}
#endif
''')
   (p/'test.cpp').write_text('''#include "play_factory.h"
#include <cassert>
#include <cstring>
static mpv_handle handle;static int created,destroyed,initialized,calls,fail,mask;static int expectedMask=127;
extern "C" mpv_handle *mpv_create(){created++;return &handle;}
extern "C" void mpv_terminate_destroy(mpv_handle*){destroyed++;}
extern "C" int mpv_set_option_string(mpv_handle*,const char *n,const char *v){calls++;if(!strcmp(n,"hwdec-software-fallback")&&!strcmp(v,"yes"))mask|=128;if(!strcmp(n,"egl-output-format")&&!strcmp(v,"rgba8"))mask|=32;if(!strcmp(n,"opengl-es")&&!strcmp(v,"yes"))mask|=64;if(!strcmp(n,"wid"))mask|=1;if(!strcmp(n,"gpu-context")&&!strcmp(v,"ohos"))mask|=2;if(!strcmp(n,"hwdec")&&!strcmp(v,"ohcodec"))mask|=4;if(!strcmp(n,"ao")&&!strcmp(v,"ohaudio"))mask|=8;if(!strcmp(n,"hwdec-software-fallback")&&!strcmp(v,"no"))mask|=16;return calls==fail?-99:0;}
extern "C" int mpv_initialize(mpv_handle*){initialized++;assert(mask==expectedMask);return fail==100?-88:0;}
int main(){p22_play_config c={"123",1280,720,0,1,"/fonts","/cache",1};for(int n=0;n<=101;n++){created=destroyed=initialized=calls=mask=0;fail=n;mpv_handle *p=nullptr;int rc=p22_play_create(&c,&p);if(n>0&&n<=calls||n==100){assert(rc<0&&!p&&destroyed==1);}else{assert(!rc&&p&&initialized==1);mpv_terminate_destroy(p);}}created=destroyed=initialized=calls=mask=fail=0;expectedMask=235;c.hardware=0;mpv_handle *sw=nullptr;assert(p22_play_create(&c,&sw)==0&&sw&&mask==235);mpv_terminate_destroy(sw);created=0;c.surface="0";mpv_handle *p=nullptr;assert(p22_play_create(&c,&p)<0&&!p&&!created);}
''')
   subprocess.run(['cc','-c',str(R/'play_policy.c'),'-o',str(p/'policy.o')],check=True)
   subprocess.run(['c++','-std=c++17','-I'+str(p),'-I'+str(R),str(p/'test.cpp'),str(R/'play_factory.cpp'),str(p/'policy.o'),'-o',str(p/'test')],check=True)
   subprocess.run([str(p/'test')],check=True)
