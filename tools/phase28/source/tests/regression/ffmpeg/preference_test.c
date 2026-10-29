#define main original_helper_suite
#include "hdr_test.c"
#undef main
#include "libavcodec/codec_internal.h"
static int receive(AVCodecContext*c,AVFrame*f){return AVERROR(EAGAIN);}
static const FFCodec fake_codec={.p.name="preference-test",.p.type=AVMEDIA_TYPE_VIDEO,.p.id=AV_CODEC_ID_HEVC,FF_CODEC_RECEIVE_FRAME_CB(receive)};
int main(int argc,char**argv){
 assert(argc==2);int prefer=!strcmp(argv[1],"prefer-packet");AVCodecContext*c=avcodec_alloc_context3(&fake_codec.p);c->width=16;c->height=16;
 if(prefer){c->side_data_prefer_packet=av_malloc(sizeof(int));c->side_data_prefer_packet[0]=-1;c->nb_side_data_prefer_packet=1;}assert(avcodec_open2(c,&fake_codec.p,NULL)==0);
 OHHdrState s={0};submit(&s,c,2000,1,19,10);AVFrame*f=av_frame_alloc();AVMasteringDisplayMetadata*m=av_mastering_display_metadata_create_side_data(f);assert(m);m->max_luminance=(AVRational){1000,1};m->has_luminance=1;AVContentLightMetadata*cll=av_content_light_metadata_create_side_data(f);cll->MaxCLL=777;
 assert(ff_oh_hdr_attach(&s,c,f,1,10)==0);m=(void*)av_frame_get_side_data(f,AV_FRAME_DATA_MASTERING_DISPLAY_METADATA)->data;cll=(void*)av_frame_get_side_data(f,AV_FRAME_DATA_CONTENT_LIGHT_LEVEL)->data;int peak=m->max_luminance.num/m->max_luminance.den;int actual_cll=cll->MaxCLL;
 printf("case=%s peak=%d cll=%d\n",argv[1],peak,actual_cll);int ok=peak==(prefer?1000:2000)&&actual_cll==(prefer?777:1000);
 av_frame_free(&f);ff_oh_hdr_uninit(&s);avcodec_free_context(&c);return ok?0:1;
}
