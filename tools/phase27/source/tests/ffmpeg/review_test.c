#define main original_suite_main
#include "hdr_test.c"
#undef main
int main(int argc,char **argv) {
 assert(argc==2); AVCodecContext*c=avcodec_alloc_context3(NULL);c->codec_id=AV_CODEC_ID_HEVC;c->internal=ff_decode_internal_alloc();assert(c->internal);OHHdrState s={0};int rc=0;
 if(!strcmp(argv[1],"unknown-normalized-zero")) {
  submit(&s,c,2000,1,19,AV_NOPTS_VALUE);submit(&s,c,1000,1,19,0);
  AVFrame*f=av_frame_alloc();assert(ff_oh_hdr_attach(&s,c,f,1,0)==0);
  AVFrameSideData*sd=av_frame_get_side_data(f,AV_FRAME_DATA_MASTERING_DISPLAY_METADATA);
  printf("CONDITIONAL_INPUT unknown2000 normalized to 0 before known1000/PTS0; attached=%d peak=%d\n",!!sd,sd?((AVMasteringDisplayMetadata*)sd->data)->max_luminance.num/10000:0);
  rc=!!sd;av_frame_free(&f);
 } else if(!strcmp(argv[1],"duplicate-third")) {
  submit(&s,c,1000,1,19,10);submit(&s,c,2000,1,19,10);output(&s,c,10,0,0);submit(&s,c,3000,1,19,10);output(&s,c,10,0,0);output(&s,c,10,0,0);assert(s.count==0);puts("PASS ambiguity survives consumption and late third member");
 } else if(!strcmp(argv[1],"output-oom")) {
  submit(&s,c,1000,1,19,10);AVFrame*f=av_frame_alloc();av_max_alloc(1);assert(ff_oh_hdr_attach(&s,c,f,1,10)==AVERROR(ENOMEM));av_max_alloc(SIZE_MAX);assert(s.count==1);av_frame_unref(f);assert(ff_oh_hdr_attach(&s,c,f,1,10)==0);assert(s.count==0);av_frame_free(&f);puts("PASS failed allocation retained queue; retry succeeds");
 } else if(!strcmp(argv[1],"existing-cll-dovi")) {
  submit(&s,c,1000,1,19,10);AVFrame*f=av_frame_alloc();AVContentLightMetadata*m=av_content_light_metadata_create_side_data(f);assert(m);m->MaxCLL=777;m->MaxFALL=123;AVFrameSideData*d=av_frame_new_side_data(f,AV_FRAME_DATA_DOVI_RPU_BUFFER,4);assert(d);memcpy(d->data,"DOVI",4);assert(ff_oh_hdr_attach(&s,c,f,1,10)==0);m=(void*)av_frame_get_side_data(f,AV_FRAME_DATA_CONTENT_LIGHT_LEVEL)->data;assert(m->MaxCLL==1000&&m->MaxFALL==0);assert(av_frame_get_side_data(f,AV_FRAME_DATA_MASTERING_DISPLAY_METADATA));assert(!memcmp(d->data,"DOVI",4));av_frame_free(&f);puts("PASS default bitstream CLL replaces old value, DOVI preserved, MDM filled");
 } else if(!strcmp(argv[1],"irap-multislice")) {
  uint8_t b[1024+AV_INPUT_BUFFER_PADDING_SIZE]={0};uint8_t tail[]={0x80},continuation[]={0,0x80};size_t n;
  submit(&s,c,1000,1,19,10);output(&s,c,10,1000,1);
  n=picture(b,1);n+=nal(b+n,36,tail,sizeof(tail));assert(ff_oh_hdr_prepare(&s,c,b,n,20,1)==0);ff_oh_hdr_commit(&s);ff_oh_hdr_finish(&s);output(&s,c,20,1000,1);assert(s.eos);
  submit(&s,c,0,0,21,30);output(&s,c,30,0,0);ff_oh_hdr_reset(&s);
  submit(&s,c,1000,1,19,10);output(&s,c,10,1000,1);submit(&s,c,0,0,16,20);output(&s,c,20,0,0);ff_oh_hdr_reset(&s);
  n=packet(b,2000,1,19);n+=nal(b+n,19,continuation,sizeof(continuation));assert(ff_oh_hdr_prepare(&s,c,b,n,30,1)==0);ff_oh_hdr_commit(&s);ff_oh_hdr_finish(&s);assert(s.count==1&&!s.disabled);output(&s,c,30,2000,1);
  submit(&s,c,1000,1,19,40);AVFrame*f=av_frame_alloc();assert(ff_oh_hdr_attach(&s,c,f,2,40)==0);assert(!f->nb_side_data&&s.count==1);av_frame_free(&f);output(&s,c,40,1000,1);
  puts("PASS EOS then CRA, BLA invalidation, multi-slice once, generation isolation");
 } else if(!strcmp(argv[1],"capacity")) {
  for(int i=0;i<OH_HDR_QUEUE_SIZE;i++)submit(&s,c,1000,1,19,i);uint8_t b[512+AV_INPUT_BUFFER_PADDING_SIZE]={0};size_t n=packet(b,2000,1,19);assert(ff_oh_hdr_prepare(&s,c,b,n,999,1)==AVERROR(ENOMEM));assert(s.count==OH_HDR_QUEUE_SIZE&&!s.pending.prepared);output(&s,c,0,1000,1);assert(ff_oh_hdr_prepare(&s,c,b,n,999,1)==0);ff_oh_hdr_commit(&s);ff_oh_hdr_finish(&s);output(&s,c,999,2000,1);puts("PASS queue bound preserves old entries and recovers after consumption");
 }else return 64;
 ff_oh_hdr_uninit(&s);av_freep(&c->internal);avcodec_free_context(&c);return rc;
}
