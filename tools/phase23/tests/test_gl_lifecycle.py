"""Compile the actual OHOS context init/uninit with injected platform failures."""
import os
from pathlib import Path
import re
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "input-package/sources/mpv/video/out/opengl/context_ohos.c"
STUBS = r"""
#include <stdbool.h>
#include <stdlib.h>
#include <stdio.h>
#include <stdarg.h>
#include <assert.h>
typedef int EGLDisplay; typedef int EGLContext; typedef int EGLSurface;
typedef int EGLConfig; typedef int EGLint; typedef int EGLNativeWindowType;
typedef int OHNativeWindow; typedef int pl_color_space_t;
struct GL {int unused;}; struct mp_image_params {int unused;};
struct vo {int alive;};
struct ra_ctx {void *priv; struct vo *vo; void *log;};
struct ra_ctx_params {pl_color_space_t (*preferred_csp)(struct ra_ctx *);
 void (*set_color)(struct ra_ctx *,struct mp_image_params *);
 void (*swap_buffers)(struct ra_ctx *);};
enum {EGL_DEFAULT_DISPLAY=1,EGL_NO_SURFACE=0,EGL_NO_CONTEXT=0,
 EGL_NATIVE_VISUAL_ID=99,GET_FORMAT=1,SET_FORMAT=2};
#define talloc_zero(ctx,type) ((type *)calloc(1,sizeof(type)))
#define MP_FATAL(...) ((void)0)
#define MP_ERR(...) ((void)0)
#define MP_WARN(...) ((void)0)
#define MP_VERBOSE(...) ((void)0)
static int fail,format,visual,set_calls,restore_calls,surface_calls;
static int surface_destroyed,context_destroyed,window_destroyed,events[32],nevents;
static bool changed;
static OHNativeWindow window=1;
static pl_color_space_t vo_ohos_preferred_csp(struct vo *v){return 0;}
static void vo_ohos_set_color(struct vo *v,struct mp_image_params *p){}
static bool vo_ohos_init(struct vo *v){v->alive=1;return true;}
static OHNativeWindow *vo_ohos_native_window(struct vo *v){return v->alive?&window:NULL;}
static void vo_ohos_uninit(struct vo *v){if(v->alive){events[nevents++]=5;window_destroyed++;v->alive=0;}}
static void ra_gl_ctx_uninit(struct ra_ctx *c){}
static bool ra_gl_ctx_init(struct ra_ctx *c,struct GL *g,struct ra_ctx_params p){return fail!=7;}
static void mpegl_load_functions(struct GL *g,void *l){}
static EGLDisplay eglGetDisplay(int x){return 1;}
static int eglInitialize(int d,void*a,void*b){return fail!=8;}
static bool mpegl_create_context(struct ra_ctx*c,int d,int*p,int*q){if(fail==9)return false;*p=1;*q=1;return true;}
static int eglGetConfigAttrib(int d,int c,int name,int*out){if(fail==1)return 0;*out=visual;return 1;}
static int OH_NativeWindow_NativeWindowHandleOpt(OHNativeWindow*w,int op,...){
 va_list a;va_start(a,op);
 if(op==GET_FORMAT){if(fail==2){va_end(a);return -1;}*va_arg(a,int*)=format;}
 else {int value=va_arg(a,int);set_calls++;
  if(!changed && fail==3){va_end(a);return -1;}
  if(changed){restore_calls++;events[nevents++]=4;if(fail==6){va_end(a);return -1;}}
  else {changed=true;events[nevents++]=1;}
  format=value;
 }
 va_end(a);return 0;
}
static int eglCreateWindowSurface(int d,int c,EGLNativeWindowType w,void*a){
 surface_calls++;events[nevents++]=2;
 return fail==4||format!=visual?0:1;
}
static int eglMakeCurrent(int d,int a,int b,int c){return c==0||fail!=5;}
static void eglDestroySurface(int d,int s){surface_destroyed++;events[nevents++]=3;}
static void eglDestroyContext(int d,int c){context_destroyed++;}
static int eglGetError(void){return 0x3009;}
static void eglSwapBuffers(int d,int s){}
"""
MAIN = r"""
int main(int argc,char**argv){
 fail=atoi(argv[1]);visual=atoi(argv[2]);int initial=atoi(argv[3]);format=initial;
 struct vo vo={0};struct ra_ctx ctx={.vo=&vo};
 bool ok=ohos_init(&ctx);
 if(fail==0||fail==6){assert(ok);assert(format==visual);assert(set_calls==1);ohos_uninit(&ctx);}
 else assert(!ok);
 assert(window_destroyed==1);assert(context_destroyed==(fail<8));
 assert(format==(fail==6?visual:initial));
 if((fail<=3 && fail!=0)||fail>=8){assert(surface_calls==0);assert(restore_calls==0);}
 else {assert(restore_calls==1);assert(surface_calls==1);}
 if(fail==0||(fail>=5&&fail<8)){assert(surface_destroyed==1);
  int a=-1,b=-1;for(int i=0;i<nevents;i++){if(events[i]==3)a=i;if(events[i]==4)b=i;}assert(a<b);}
 ohos_uninit(&ctx);assert(context_destroyed==(fail<8));assert(window_destroyed==1);
 assert(surface_destroyed==(fail==0||(fail>=5&&fail<8)));free(ctx.priv);
 if(fail==6){
  fail=0;changed=false;set_calls=0;restore_calls=0;
  assert(ohos_init(&ctx));ohos_uninit(&ctx);assert(restore_calls==1);free(ctx.priv);
 }
 puts("PASS");return 0;
}
"""

class Lifecycle(unittest.TestCase):
    def test_actual_init_teardown_and_failure_paths(self):
        code=SOURCE.read_text().split("static bool ohos_reconfig")[0]
        code=re.sub(r'^#include.*$', '', code, flags=re.M)
        with tempfile.TemporaryDirectory() as directory:
            source=Path(directory)/"probe.c"; binary=Path(directory)/"probe"
            source.write_text(STUBS+code+MAIN)
            subprocess.run(["/usr/bin/clang","-std=c11","-Wno-pointer-to-int-cast",
                            str(source),"-o",str(binary)],check=True)
            for failure in (0,1,2,3,4,5,6,7,8,9):
                for visual in (11,12,34,35):
                    for initial in (visual,34):
                        with self.subTest(failure=failure,visual=visual,initial=initial):
                            p=subprocess.run([str(binary),str(failure),str(visual),str(initial)],
                                             capture_output=True,text=True)
                            self.assertEqual(p.returncode,0,p.stderr)

if __name__=="__main__": unittest.main()
