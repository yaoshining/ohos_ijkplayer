from pathlib import Path
import subprocess,tempfile,unittest
ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/"input-package/sources/mpv/video/out/hwdec/hwdec_ohcodec_pl.c"
STUBS=r"""
#include <assert.h>
#include <stdlib.h>
#include <stdbool.h>
#define NATIVE_ERROR_OK 0
#define P23_TRACE(...) ((void)0)
#define MP_ERR(...) ((void)0)
typedef struct {int refs;} OHNativeWindowBuffer;
struct surface {void*image;};struct ohcodec_priv {struct surface*surface;};
struct owner {void*priv;};struct ra_hwdec_mapper {struct owner*owner;};
static int rc,system_closed,caller_closed,unrefs;
static int OH_NativeWindow_NativeObjectUnreference(OHNativeWindowBuffer*b){assert(b->refs>0);b->refs--;unrefs++;return 0;}
static int OH_NativeImage_ReleaseNativeWindowBuffer(void*i,OHNativeWindowBuffer*b,int fd){
 assert(b->refs>0);if(fd>=0)system_closed++;if(rc==0)OH_NativeWindow_NativeObjectUnreference(b);return rc;
}
static int close(int fd){caller_closed++;return 0;}
"""
MAIN=r"""
int main(int argc,char**argv){
 rc=atoi(argv[1]);struct surface surface={(void*)1};struct ohcodec_priv p={&surface};
 struct owner o={&p};struct ra_hwdec_mapper mapper={&o};OHNativeWindowBuffer b={2};
 release_acquired_buffer(&mapper,&b,9);
 assert(b.refs==0);assert(unrefs==2);assert(system_closed==1);assert(caller_closed==0);
 release_acquired_buffer(&mapper,NULL,-1);assert(unrefs==2);return 0;
}
"""
class Release(unittest.TestCase):
 def test_acquired_wrapper_and_fence_on_success_and_failed_queue_return(self):
  s=SOURCE.read_text();a=s.index("static void release_acquired_buffer(");b=s.index("static void release_window_buffer(",a)
  with tempfile.TemporaryDirectory() as d:
   p=Path(d);(p/"test.c").write_text(STUBS+s[a:b]+MAIN)
   subprocess.run(["/usr/bin/clang","-std=c11",str(p/"test.c"),"-o",str(p/"test")],check=True)
   for rc in (0,41210000,41207000):
    with self.subTest(rc=rc):
     r=subprocess.run([str(p/"test"),str(rc)],capture_output=True,text=True);self.assertEqual(r.returncode,0,r.stderr)
 def test_extra_reference_failure_returns_acquired_reference(self):
  s=SOURCE.read_text();a=s.index("    if (OH_NativeWindow_NativeObjectReference(wb)");b=s.index("    if (OH_NativeBuffer_FromNativeWindowBuffer",a)
  fragment=s[a:b]
  harness=r"""
#define NATIVE_ERROR_UNKNOWN -1
static int OH_NativeWindow_NativeObjectReference(OHNativeWindowBuffer*b){return -1;}
static int attempt(struct ohcodec_priv*owner,OHNativeWindowBuffer*wb,int fence_fd){
""" + fragment + r"""
 return 0;
}
int main(int argc,char**argv){
 rc=atoi(argv[1]);struct surface surface={(void*)1};struct ohcodec_priv owner={&surface};
 OHNativeWindowBuffer b={1};assert(attempt(&owner,&b,9)==NATIVE_ERROR_UNKNOWN);
 assert(b.refs==0);assert(unrefs==1);assert(system_closed==1);assert(caller_closed==0);
 return 0;
}
"""
  with tempfile.TemporaryDirectory() as d:
   p=Path(d);(p/"test.c").write_text(STUBS+harness)
   subprocess.run(["/usr/bin/clang","-std=c11",str(p/"test.c"),"-o",str(p/"test")],check=True)
   for rc in (0,41210000,41207000):
    with self.subTest(rc=rc):
     r=subprocess.run([str(p/"test"),str(rc)],capture_output=True,text=True);self.assertEqual(r.returncode,0,r.stderr)
if __name__=="__main__":unittest.main()
