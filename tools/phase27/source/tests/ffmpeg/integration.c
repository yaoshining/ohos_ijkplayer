#define main helper_tests_main
#include "hdr_test.c"
#undef main
#include <errno.h>
#include <stdbool.h>
typedef int OH_AVErrCode;
typedef struct {int size,offset;int64_t pts;unsigned flags;} OH_AVCodecBufferAttr;
typedef struct {uint8_t data[512];int capacity;OH_AVCodecBufferAttr attr;} OH_AVBuffer;
typedef struct {int index;OH_AVBuffer*buffer;uint64_t generation;} OHCodecDecQueueItem;
typedef struct {AVPacket pkt;OHHdrState hdr;int *dec;bool eof_sent,got_stream_info,output_to_window;} OHCodecDecContext;
typedef struct {int unused;} OH_AVFormat;
enum {AV_ERR_OK=0,AVCODEC_BUFFER_FLAGS_EOS=1,AVCODEC_BUFFER_FLAGS_SYNC_FRAME=2};
static int fail_attr,fail_push,pushes,freed;
static uint8_t *OH_AVBuffer_GetAddr(OH_AVBuffer*b){return b->data;}
static int OH_AVBuffer_GetCapacity(OH_AVBuffer*b){return b->capacity;}
static int OH_AVBuffer_SetBufferAttr(OH_AVBuffer*b,const OH_AVCodecBufferAttr*a){if(fail_attr)return 1;b->attr=*a;return 0;}
static int OH_AVBuffer_GetBufferAttr(OH_AVBuffer*b,OH_AVCodecBufferAttr*a){*a=b->attr;return 0;}
static int OH_VideoDecoder_PushInputBuffer(int*d,int i){(void)d;(void)i;if(fail_push)return 1;pushes++;return 0;}
static int OH_VideoDecoder_FreeOutputBuffer(int*d,int i){(void)d;(void)i;freed++;return 0;}
static OH_AVFormat*OH_VideoDecoder_GetOutputDescription(int*d){(void)d;return NULL;}
static void OH_AVFormat_Destroy(OH_AVFormat*f){(void)f;}
static void oh_decode_on_stream_changed(int*d,OH_AVFormat*f,AVCodecContext*c){(void)d;(void)f;(void)c;}
static int ff_oh_err_to_ff_err(int rc){return rc?AVERROR(EIO):0;}
static int oh_decode_wrap_hw_buffer(AVCodecContext*c,AVFrame*f,OHCodecDecQueueItem*q,const OH_AVCodecBufferAttr*a){(void)c;(void)f;(void)q;(void)a;return 0;}
static int oh_decode_wrap_sw_buffer(AVCodecContext*c,AVFrame*f,OHCodecDecQueueItem*q,const OH_AVCodecBufferAttr*a){return oh_decode_wrap_hw_buffer(c,f,q,a);}
#include "ohdec-functions.inc"
int main(int argc,char**argv){
 assert(argc==2);AVCodecContext*c=avcodec_alloc_context3(NULL);c->codec_id=AV_CODEC_ID_HEVC;c->pkt_timebase=AV_TIME_BASE_Q;c->internal=ff_decode_internal_alloc();assert(c->internal);
 OHCodecDecContext s={0};c->priv_data=&s;s.got_stream_info=true;s.output_to_window=true;
 OH_AVBuffer buffer={.capacity=8};OHCodecDecQueueItem q={.index=3,.buffer=&buffer,.generation=1};
 assert(av_new_packet(&s.pkt,32)==0);memset(s.pkt.data,0,32);s.pkt.pts=10;
 prepare(&s.hdr,c,1000,1,19,10);
 if(!strcmp(argv[1],"publication")){
  fail_attr=1;assert(oh_decode_send_pkt(c,&q)<0);assert(!s.hdr.count&&s.pkt.size==32&&!pushes);fail_attr=0;
  fail_push=1;assert(oh_decode_send_pkt(c,&q)<0);assert(!s.hdr.count&&s.pkt.size==32&&!pushes);fail_push=0;
  assert(oh_decode_send_pkt(c,&q)==0);assert(s.hdr.count==1&&s.hdr.pending.committed&&s.pkt.size==24);
  fail_push=1;assert(oh_decode_send_pkt(c,&q)<0);assert(s.hdr.count==1&&s.pkt.size==24);fail_push=0;
  for(int i=0;i<3;i++)assert(oh_decode_send_pkt(c,&q)==0);
  assert(s.hdr.count==1&&!s.hdr.pending.prepared&&!s.pkt.size&&pushes==4);output(&s.hdr,c,10,1000,1);
 }else{
  ff_oh_hdr_commit(&s.hdr);ff_oh_hdr_finish(&s.hdr);buffer.attr.pts=10;
  AVFrame*f=av_frame_alloc();if(!strcmp(argv[1],"software"))s.output_to_window=false;
  assert(oh_decode_output_frame(c,f,&q)==0);assert(av_frame_get_side_data(f,AV_FRAME_DATA_MASTERING_DISPLAY_METADATA));assert(av_frame_get_side_data(f,AV_FRAME_DATA_CONTENT_LIGHT_LEVEL));av_frame_free(&f);
 }
 ff_oh_hdr_uninit(&s.hdr);av_packet_unref(&s.pkt);c->priv_data=NULL;av_freep(&c->internal);avcodec_free_context(&c);puts("PASS actual ohdec integration");return 0;
}
