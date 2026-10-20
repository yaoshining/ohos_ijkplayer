from pathlib import Path
import subprocess
import tempfile
import unittest
ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/"input-package/sources/mpv/video/out/hwdec/hwdec_ohcodec_pl.c"
STUBS=r"""
#include <stdbool.h>
#include <stdlib.h>
#include <assert.h>
#define P23_TRACE(...) ((void)0)
typedef int VkDevice;typedef void* pl_tex;
struct ra_tex {void *priv;};
struct vk_import {struct ra_tex*ratex;pl_tex pltex;void*native_buffer;int release_sem,acquire_sem,view,image,memory;unsigned seq;};
struct vk {int device;};
struct vk_mapper {struct vk*vk;void*gpu;};
struct ohcodec_mapper_priv {void*priv;};
struct ra_hwdec_mapper {void*priv;void*ra;struct ra_tex*tex[1];};
static int texture_freed,buffer_freed;
static void pl_tex_destroy(void*g,pl_tex*t){if(*t)texture_freed++;*t=NULL;}
static void ra_tex_free(void*r,struct ra_tex**t){if(*t){pl_tex_destroy(NULL,&(*t)->priv);free(*t);*t=NULL;}}
static void vkDestroySemaphore(int d,int x,void*a){}
static void vkDestroyImageView(int d,int x,void*a){}
static void vkDestroyImage(int d,int x,void*a){}
static void vkFreeMemory(int d,int x,void*a){}
static void OH_NativeBuffer_Unreference(void*b){buffer_freed++;}
#define talloc_free free
"""
MAIN=r"""
int main(int argc,char**argv){
 int mode=atoi(argv[1]);struct vk vk={1};struct vk_mapper v={.vk=&vk};
 struct ohcodec_mapper_priv p={.priv=&v};struct ra_hwdec_mapper m={.priv=&p};
 struct vk_import*e=calloc(1,sizeof(*e));e->pltex=(void*)1;e->native_buffer=(void*)2;
 if(mode){e->ratex=calloc(1,sizeof(*e->ratex));e->ratex->priv=e->pltex;m.tex[0]=e->ratex;}
 destroy_import(&m,e);assert(texture_freed==1);assert(buffer_freed==1);assert(!m.tex[0]);
 destroy_import(&m,NULL);assert(texture_freed==1);return 0;
}
"""
class Release(unittest.TestCase):
 def test_texture_created_but_ra_allocation_failed(self):
  code=SOURCE.read_text();start=code.index("static void destroy_import(");end=code.index("static VkFilter",start)
  with tempfile.TemporaryDirectory() as d:
   p=Path(d);(p/"test.c").write_text(STUBS+code[start:end]+MAIN)
   subprocess.run(["/usr/bin/clang","-std=c11",str(p/"test.c"),"-o",str(p/"test")],check=True)
   for mode in (0,1):
    with self.subTest(mode=mode):
     r=subprocess.run([str(p/"test"),str(mode)],capture_output=True,text=True)
     self.assertEqual(r.returncode,0,r.stderr)
if __name__=="__main__":unittest.main()
