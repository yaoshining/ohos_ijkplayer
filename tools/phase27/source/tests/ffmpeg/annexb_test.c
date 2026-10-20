#define main original_helper_suite
#include "hdr_test.c"
#undef main
#include "libavcodec/bsf/hevc_mp4toannexb.c"
int main(int argc, char **argv) {
 assert(argc==2);int changed=strcmp(argv[1],"extradata-only")!=0;
 AVBSFContext*b=NULL;assert(av_bsf_alloc(&ff_hevc_mp4toannexb_bsf.p,&b)==0);
 b->par_in->codec_id=AV_CODEC_ID_HEVC;b->par_in->codec_type=AVMEDIA_TYPE_VIDEO;b->time_base_in=AV_TIME_BASE_Q;
 uint8_t old[256]={0},now[512]={0};size_t oldn=sei(old,137,1000)-4;
 b->par_in->extradata_size=28+oldn;b->par_in->extradata=av_mallocz(b->par_in->extradata_size+AV_INPUT_BUFFER_PADDING_SIZE);
 uint8_t*e=b->par_in->extradata;e[0]=1;e[21]=3;e[22]=1;e[23]=39;AV_WB16(e+24,1);AV_WB16(e+26,oldn);memcpy(e+28,old+4,oldn);assert(av_bsf_init(b)==0);
 size_t n=0;uint8_t ps[]={0x80};
 if(!strcmp(argv[1],"sei-after-ps")){size_t z=nal(now,32,ps,1);AV_WB32(now,z-4);n+=z;}
 if(changed){size_t z=sei(now+n,137,2000);AV_WB32(now+n,z-4);n+=z;}
 if(!strcmp(argv[1],"sei-before-ps")){size_t z=nal(now+n,32,ps,1);AV_WB32(now+n,z-4);n+=z;}
 size_t z=picture(now+n,!strcmp(argv[1],"non-irap")?1:19);AV_WB32(now+n,z-4);n+=z;
 AVPacket*in=av_packet_alloc(),*out=av_packet_alloc();assert(av_new_packet(in,n)==0);memcpy(in->data,now,n);in->pts=10;assert(av_bsf_send_packet(b,in)==0);assert(av_bsf_receive_packet(b,out)==0);
 AVCodecContext*c=avcodec_alloc_context3(NULL);c->codec_id=AV_CODEC_ID_HEVC;c->internal=ff_decode_internal_alloc();OHHdrState s={0};
 assert(out->pts==10);assert(ff_oh_hdr_prepare(&s,c,out->data,out->size,10,1)==0);
 assert(s.packet.nb_nals==(!strcmp(argv[1],"non-irap")?2:!strncmp(argv[1],"sei-",4)?4:changed?3:2));ff_oh_hdr_commit(&s);ff_oh_hdr_finish(&s);
 AVFrame*f=av_frame_alloc();assert(ff_oh_hdr_attach(&s,c,f,1,10)==0);AVFrameSideData*sd=av_frame_get_side_data(f,AV_FRAME_DATA_MASTERING_DISPLAY_METADATA);assert(sd);AVMasteringDisplayMetadata*m=(void*)sd->data;int peak=m->max_luminance.num/m->max_luminance.den;
 printf("case=%s expected=%d actual=%d\n",argv[1],changed?2000:1000,peak);
 av_frame_free(&f);ff_oh_hdr_uninit(&s);av_freep(&c->internal);avcodec_free_context(&c);av_packet_free(&in);av_packet_free(&out);av_bsf_free(&b);return peak==(changed?2000:1000)?0:1;
}
