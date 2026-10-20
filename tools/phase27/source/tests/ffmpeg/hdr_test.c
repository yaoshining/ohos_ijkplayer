#include <assert.h>
#include <stdio.h>
#include <string.h>
#include "libavcodec/avcodec_internal.h"
#include "libavcodec/ohcodec_hdr.h"
#include "libavutil/intreadwrite.h"
#include "libavutil/mastering_display_metadata.h"
#include "libavutil/mem.h"

/* 测试仅编码输入夹具；被测解析/转换和状态机必须来自生产源码。 */
static size_t nal(uint8_t *out, int type, const uint8_t *payload, size_t n) {
    out[0]=out[1]=out[2]=0;out[3]=1;out[4]=type<<1;out[5]=1;
    size_t w=6;unsigned zeros=0;
    for(size_t i=0;i<n;i++){if(zeros>=2&&payload[i]<=3){out[w++]=3;zeros=0;}out[w++]=payload[i];zeros=payload[i]?0:zeros+1;}
    return w;
}
static size_t sei(uint8_t *out,int type,int peak) {
    uint8_t b[64]={0};size_t n=type==137?24:4;b[0]=type;b[1]=n;
    if(type==137){unsigned xy[]={8500,39850,6550,2300,35400,14600,15635,16450};for(int i=0;i<8;i++)AV_WB16(b+2+2*i,xy[i]);AV_WB32(b+18,peak*10000);AV_WB32(b+22,0);}
    else {AV_WB16(b+2,1000);AV_WB16(b+4,0);}
    b[n+2]=0x80;return nal(out,39,b,n+3);
}
static size_t picture(uint8_t *out,int type){uint8_t p[]={0x80,0x80};return nal(out,type,p,sizeof(p));}
static size_t packet(uint8_t *out,int peak,int cll,int type){size_t n=0;if(peak)n+=sei(out+n,137,peak);if(cll)n+=sei(out+n,144,0);return n+picture(out+n,type);}
static void prepare(OHHdrState *s,AVCodecContext*c,int peak,int cll,int type,int64_t pts) {
    uint8_t b[512+AV_INPUT_BUFFER_PADDING_SIZE]={0};size_t n=packet(b,peak,cll,type);
    assert(ff_oh_hdr_prepare(s,c,b,n,pts,1)==0);
}
static void submit(OHHdrState*s,AVCodecContext*c,int peak,int cll,int type,int64_t pts){prepare(s,c,peak,cll,type,pts);ff_oh_hdr_commit(s);ff_oh_hdr_finish(s);}
static void output(OHHdrState*s,AVCodecContext*c,int64_t pts,int peak,int cll){
    AVFrame*f=av_frame_alloc();assert(f);assert(ff_oh_hdr_attach(s,c,f,1,pts)==0);
    AVFrameSideData*md=av_frame_get_side_data(f,AV_FRAME_DATA_MASTERING_DISPLAY_METADATA),*cd=av_frame_get_side_data(f,AV_FRAME_DATA_CONTENT_LIGHT_LEVEL);
    if(peak){assert(md);AVMasteringDisplayMetadata*m=(void*)md->data;assert(m->has_luminance&&m->has_primaries);assert(m->max_luminance.num==peak*10000&&m->max_luminance.den==10000);assert(m->min_luminance.num==0&&m->min_luminance.den==10000);assert(m->display_primaries[0][0].num==35400&&m->display_primaries[0][0].den==50000);}else assert(!md);
    if(cll){assert(cd);AVContentLightMetadata*m=(void*)cd->data;assert(m->MaxCLL==1000&&m->MaxFALL==0);}else assert(!cd);
    av_frame_free(&f);
}
int main(void){
 AVCodecContext*c=avcodec_alloc_context3(NULL);assert(c);c->codec_id=AV_CODEC_ID_HEVC;c->internal=ff_decode_internal_alloc();assert(c->internal);OHHdrState s={0};
 submit(&s,c,1000,1,19,10);submit(&s,c,2000,1,19,20);output(&s,c,20,2000,1);output(&s,c,10,1000,1);puts("PASS reordered snapshots, both CLL1000");ff_oh_hdr_reset(&s);
 submit(&s,c,1000,0,19,10);output(&s,c,10,1000,0);ff_oh_hdr_reset(&s);submit(&s,c,0,1,19,10);output(&s,c,10,0,1);puts("PASS independent MDM CLL");ff_oh_hdr_reset(&s);
 prepare(&s,c,1000,1,19,10);output(&s,c,10,0,0);assert(!s.current.mastering_display.present);ff_oh_hdr_commit(&s);ff_oh_hdr_commit(&s);ff_oh_hdr_finish(&s);output(&s,c,10,1000,1);output(&s,c,10,0,0);puts("PASS prepare not published, commit once");ff_oh_hdr_reset(&s);
 submit(&s,c,1000,1,19,10);submit(&s,c,2000,1,19,10);output(&s,c,10,0,0);output(&s,c,10,0,0);submit(&s,c,1000,1,19,AV_NOPTS_VALUE);output(&s,c,AV_NOPTS_VALUE,0,0);puts("PASS duplicate unknown PTS no misattach");ff_oh_hdr_reset(&s);
 submit(&s,c,1000,1,19,10);output(&s,c,10,1000,1);submit(&s,c,0,0,21,20);output(&s,c,20,1000,1);submit(&s,c,0,0,19,30);output(&s,c,30,0,0);puts("PASS normal CRA persists, IDR clears");ff_oh_hdr_reset(&s);
 submit(&s,c,1000,1,19,10);ff_oh_hdr_reset(&s);output(&s,c,10,0,0);submit(&s,c,0,0,1,20);output(&s,c,20,0,0);puts("PASS flush removes state and pending");ff_oh_hdr_reset(&s);
 {uint8_t b[256+AV_INPUT_BUFFER_PADDING_SIZE]={0},bad[]={137,24,0x80};size_t n=nal(b,39,bad,sizeof(bad));assert(ff_oh_hdr_prepare(&s,c,b,n,10,1)<0);assert(!s.pending.prepared&&!s.current.mastering_display.present);puts("PASS malformed SEI atomic failure");}
 {submit(&s,c,1000,1,19,10);AVFrame*f=av_frame_alloc();AVMasteringDisplayMetadata*m=av_mastering_display_metadata_create_side_data(f);assert(m);m->max_luminance=(AVRational){777,1};assert(ff_oh_hdr_attach(&s,c,f,1,10)==0);m=(void*)av_frame_get_side_data(f,AV_FRAME_DATA_MASTERING_DISPLAY_METADATA)->data;assert(m->max_luminance.num==1000*10000);assert(av_frame_get_side_data(f,AV_FRAME_DATA_CONTENT_LIGHT_LEVEL));av_frame_free(&f);puts("PASS default bitstream MDM replaces old frame MDM, missing CLL filled");ff_oh_hdr_reset(&s);}
 {uint8_t b[512+AV_INPUT_BUFFER_PADDING_SIZE]={0};size_t n=packet(b,1000,1,19);n+=picture(b+n,1);assert(ff_oh_hdr_prepare(&s,c,b,n,10,1)==0);ff_oh_hdr_commit(&s);ff_oh_hdr_finish(&s);output(&s,c,10,0,0);assert(s.disabled);puts("PASS multi picture decodes without misleading HDR");ff_oh_hdr_reset(&s);}
 {av_max_alloc(1);uint8_t b[512+AV_INPUT_BUFFER_PADDING_SIZE]={0};size_t n=packet(b,1000,1,19);assert(ff_oh_hdr_prepare(&s,c,b,n,10,1)==AVERROR(ENOMEM));av_max_alloc(SIZE_MAX);assert(!s.pending.prepared);puts("PASS splitter OOM atomic");}
 ff_oh_hdr_uninit(&s);av_freep(&c->internal);avcodec_free_context(&c);return 0;
}
