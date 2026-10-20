"""Execute real FFmpeg functions against allocation and OHCodec failure stubs."""
from pathlib import Path
import subprocess,tempfile,unittest
ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/"ffmpeg-input/source/libavcodec/ohdec.c"
def function(text,name):
 start=text.index(name+"(");start=text.rfind("\n",0,start)+1
 a=text.index("{",start);depth=1;b=a+1
 while depth:
  depth+=(text[b]=="{")-(text[b]=="}");b+=1
 return text[start:b]+"\n"
STUBS=r"""
#include <stdbool.h>
#include <stdint.h>
#include <stdlib.h>
#include <stdio.h>
#include <assert.h>
#include <errno.h>
#include <stdatomic.h>
#define AVERROR(x) (-(x))
#define AVERROR_BUG -100
#define AVERROR_EXTERNAL -101
#define AV_LOG_ERROR 1
#define AV_LOG_DEBUG 2
#define AV_LOG_WARNING 3
#define AV_ERR_OK 0
#define HARDWARE 1
#define SOFTWARE 2
#define AV_PIX_FMT_OHCODEC 7
#define AV_BUFFER_FLAG_READONLY 1
#define AV_TIME_BASE_Q 1
#define AV_NOPTS_VALUE -1
typedef int OH_AVCodec;typedef int OH_AVErrCode;typedef int OH_AVCapability;
typedef struct base {uint8_t*data;void(*free_cb)(void*,uint8_t*);void*opaque;int refs;} base;
typedef struct AVBufferRef {uint8_t*data;base*b;} AVBufferRef;
typedef struct {OH_AVCodec*dec;atomic_uint generation;} OHCodecDecRef;
typedef struct {AVBufferRef*dec_ref;unsigned index,generation;atomic_bool released;} AVOHCodecBuffer;
typedef struct {const char*name;bool allow_sw;OH_AVCodec*dec;AVBufferRef*dec_ref;int width,height;} OHCodecDecContext;
typedef struct {void*priv_data;int codec_id,pkt_timebase;AVBufferRef*hw_frames_ctx;} AVCodecContext;
typedef struct {int width,height,format;AVBufferRef*buf[1];AVBufferRef*hw_frames_ctx;uint8_t*data[4];int64_t pts,pkt_dts;} AVFrame;
typedef struct {unsigned index,generation;} OHCodecDecQueueItem;
typedef struct {int64_t pts;} OH_AVCodecBufferAttr;
static int fail,malloc_calls,buffer_calls,ref_calls,live,destroyed,freed_output;
static OH_AVCodec codec;
static void*av_mallocz(size_t n){malloc_calls++;if((fail==1&&malloc_calls==1)||(fail==4&&malloc_calls==2))return NULL;live++;return calloc(1,n);}
static void av_free(void*p){if(p){live--;free(p);}}
static AVBufferRef*av_buffer_create(uint8_t*d,size_t n,void(*cb)(void*,uint8_t*),void*o,int f){
 buffer_calls++;if((fail==2&&buffer_calls==1)||(fail==6&&buffer_calls==2))return NULL;
 base*b=calloc(1,sizeof(*b));*b=(base){d,cb,o,1};AVBufferRef*r=calloc(1,sizeof(*r));*r=(AVBufferRef){d,b};return r;
}
static AVBufferRef*av_buffer_ref(AVBufferRef*r){ref_calls++;if((fail==5&&ref_calls==1)||(fail==7&&ref_calls==2))return NULL;
 assert(r);AVBufferRef*n=calloc(1,sizeof(*n));*n=*r;n->b->refs++;return n;}
static void av_buffer_unref(AVBufferRef**p){if(!*p)return;AVBufferRef*r=*p;*p=NULL;if(--r->b->refs==0){if(r->b->free_cb)r->b->free_cb(r->b->opaque,r->data);free(r->b);}free(r);}
static int OH_VideoDecoder_Destroy(OH_AVCodec*d){assert(d==&codec);destroyed++;return 0;}
static OH_AVCodec*OH_VideoDecoder_CreateByName(const char*n){return &codec;}
static int OH_VideoDecoder_FreeOutputBuffer(OH_AVCodec*d,unsigned i){assert(d==&codec&&i==9);freed_output++;return 0;}
static int OH_VideoDecoder_RenderOutputBuffer(OH_AVCodec*d,unsigned i){return 0;}
static const char*ff_oh_mime(int i,void*a){return "video/avc";}
static OH_AVCapability*OH_AVCodec_GetCapabilityByCategory(const char*m,bool e,int c){return &codec;}
static const char*OH_AVCapability_GetName(void*c){return "codec";}
static int ff_oh_err_to_ff_err(int e){return e?-1:0;}
static const char*av_err2str(int x){return "";}
static void av_log(void*p,int l,const char*f,...){}
static int ff_decode_frame_props(void*a,void*b){return fail==3?-33:0;}
static int64_t av_rescale_q(int64_t a,int b,int c){return a;}
static int oh_decode_attach_dovi(void*a,void*b,int64_t pts){return fail==8?-88:0;}
"""
MAIN=r"""
int main(int argc,char**argv){
 fail=atoi(argv[1]);int stale=atoi(argv[2]);OHCodecDecContext s={.name="codec",.width=10,.height=10};
 AVCodecContext av={.priv_data=&s};int rc=oh_decode_create(&s,&av);
 if(fail==1||fail==2){assert(rc<0);assert(!s.dec&&!s.dec_ref);assert(destroyed==1&&live==0);return 0;}
 assert(rc==0);uint8_t dummy=0;int saved_fail=fail;fail=0;
 av.hw_frames_ctx=av_buffer_create(&dummy,1,NULL,NULL,0);fail=saved_fail;
 /* Account for the unrelated hw_frames context outside injected call counts. */
 buffer_calls--;
 AVFrame frame={0};OHCodecDecQueueItem out={9,stale?1:0};OH_AVCodecBufferAttr attr={0};
 rc=oh_decode_wrap_hw_buffer(&av,&frame,&out,&attr);
 if(fail>=3)assert(rc<0);else assert(rc==0);
 av_buffer_unref(&frame.buf[0]);av_buffer_unref(&frame.hw_frames_ctx);
 assert(freed_output==(stale?0:1));av_buffer_unref(&s.dec_ref);s.dec=NULL;av_buffer_unref(&av.hw_frames_ctx);
 assert(destroyed==1);assert(live==0);return 0;
}
"""
class Decoder(unittest.TestCase):
 def test_allocations_normal_close_and_stale_outputs(self):
  source=SOURCE.read_text()
  names=["oh_decode_release","oh_decode_create","av_ohcodec_release_buffer","oh_buffer_release"]
  if "oh_decode_discard_output(" in source:names.append("oh_decode_discard_output")
  names.append("oh_decode_wrap_hw_buffer")
  code=STUBS+"".join(function(source,n)for n in names)+MAIN
  with tempfile.TemporaryDirectory() as d:
   p=Path(d);(p/"test.c").write_text(code)
   subprocess.run(["/usr/bin/clang","-std=c11",str(p/"test.c"),"-o",str(p/"test")],check=True)
   for failure in range(9):
    for stale in (0,1):
     with self.subTest(failure=failure,stale=stale):
      r=subprocess.run([str(p/"test"),str(failure),str(stale)],capture_output=True,text=True)
      self.assertEqual(r.returncode,0,r.stderr)
if __name__=="__main__":unittest.main()
