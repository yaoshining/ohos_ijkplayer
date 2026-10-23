#include "hdr_contract.h"
#include <native_image/native_image.h>
#include <native_buffer/native_buffer.h>
#include <condition_variable>
extern "C" {
#include <libavformat/avformat.h>
#include <libavcodec/avcodec.h>
#include <libavcodec/ohcodec_buffer.h>
#include <libavutil/hwcontext.h>
#include <libavutil/hwcontext_oh.h>
#include <libavutil/pixdesc.h>
}
static void p26Available(void*opaque){((p26::CallbackState*)opaque)->signal();}
static int p26Release(void*i,void*b,int fd){return OH_NativeImage_ReleaseNativeWindowBuffer((OH_NativeImage*)i,(OHNativeWindowBuffer*)b,fd);}
static int p26Unref(void*b){return OH_NativeWindow_NativeObjectUnreference(b);}
static void execute_direct(Job&j){
 auto&tl=*j.timeline;p25::workerSession=&tl;auto runKey=tl.emit(p25::Lane::Worker,p25::Event::RunBegin,j.sequence,j.sequence);
 std::ofstream f(j.root+"/"+j.mode+"-"+std::to_string(j.sequence)+".log");
 const bool hw=p24::hardwareForMode(j.mode);std::string sample=j.mode.find("pq2")!=std::string::npos?"pq2":j.mode.find("hlg")!=std::string::npos?"hlg":j.mode.find("sdr")!=std::string::npos?"sdr":"pq";
 std::string path=j.root+"/"+sample+"-bounded.mp4";
 log(f,"P26_BEGIN sample="+sample+" hardware="+std::to_string(hw)+" pid="+std::to_string(getpid())+" fixtureSHA256="+hashfile(path));
 AVFormatContext*fmt=nullptr;AVCodecContext*dec=nullptr;AVBufferRef*dev=nullptr;AVFrame*frame=av_frame_alloc();AVPacket*pkt=av_packet_alloc();OH_NativeImage*image=nullptr;p26::CallbackState*notify=nullptr;bool listener=false,success=false;std::string reason="not_started";int rc=0;
 auto cleanup=[&]{av_packet_free(&pkt);av_frame_free(&frame);if(dec)tl.query(103,[&]{avcodec_free_context(&dec);return 0;});av_buffer_unref(&dev);avformat_close_input(&fmt);if(image){if(notify)notify->retire();if(listener){int u=OH_NativeImage_UnsetOnFrameAvailableListener(image);log(f,"P26_UNSET rc="+std::to_string(u));if(u){success=false;reason="unset_listener_failed";}}OH_NativeImage_Destroy(&image);if(notify)log(f,"P26_CALLBACK retired=1 processLifetime=1 late="+std::to_string(notify->late()));}log(f,"P26_RESULT decoded="+std::to_string(success)+" reason="+reason+" stopped="+std::to_string(stopping));j.result="decoded="+std::to_string(success)+" reason="+reason;tl.emit(p25::Lane::Worker,p25::Event::RunEnd,runKey,j.sequence);p25::workerSession=nullptr;};
 do {
  if(!frame||!pkt){reason="allocation";break;}if(!maps(j.root,f)){reason="maps";break;}
  rc=avformat_open_input(&fmt,path.c_str(),nullptr,nullptr);if(rc<0){reason="input_"+std::to_string(rc);break;}
  rc=avformat_find_stream_info(fmt,nullptr);if(rc<0){reason="stream_info_"+std::to_string(rc);break;}
  int stream=av_find_best_stream(fmt,AVMEDIA_TYPE_VIDEO,-1,-1,nullptr,0);if(stream<0){reason="video_stream";break;}
  const AVCodec*codec=avcodec_find_decoder_by_name(hw?"hevc_ohcodec":"hevc");if(!codec){reason="decoder_missing";break;}
  dec=avcodec_alloc_context3(codec);if(!dec){reason="codec_alloc";break;}
  rc=avcodec_parameters_to_context(dec,fmt->streams[stream]->codecpar);if(rc<0){reason="parameters";break;}dec->pkt_timebase=fmt->streams[stream]->time_base;
  log(f,"P26_INPUT decoder="+std::string(codec->name)+" codedSideData="+std::to_string(dec->nb_coded_side_data)+" width="+std::to_string(dec->width)+" height="+std::to_string(dec->height));
  if(hw){image=OH_ConsumerSurface_Create();if(!image){reason="consumer_create";break;}notify=p26::acquireCallbackState();if(!notify){reason="callback_slot_limit";break;}OH_OnFrameAvailableListener l{notify,p26Available};rc=OH_NativeImage_SetOnFrameAvailableListener(image,l);if(rc){reason="listener_"+std::to_string(rc);break;}listener=true;
   auto*window=OH_NativeImage_AcquireNativeWindow(image);if(!window){reason="consumer_window";break;}
   dev=av_hwdevice_ctx_alloc(AV_HWDEVICE_TYPE_OHCODEC);if(!dev){reason="hw_alloc";break;}auto*ctx=(AVHWDeviceContext*)dev->data;((AVOHCodecDeviceContext*)ctx->hwctx)->native_window=window;
   rc=av_hwdevice_ctx_init(dev);if(rc<0){reason="hw_init_"+std::to_string(rc);break;}dec->hw_device_ctx=av_buffer_ref(dev);if(!dec->hw_device_ctx){reason="hw_ref";break;}
  }
  AVDictionary*options=nullptr;if(hw)av_dict_set(&options,"allow_sw","0",0);
  rc=tl.query(100,[&]{return avcodec_open2(dec,codec,&options);});int unused=av_dict_count(options);av_dict_free(&options);if(rc<0||unused){reason="open_"+std::to_string(rc)+"_unused_"+std::to_string(unused);break;}
  bool pending=false,draining=false,drainSent=false;double deadline=mono()+25;
  while(!stopping&&mono()<deadline){
   rc=tl.query(102,[&]{return avcodec_receive_frame(dec,frame);});if(rc==0){success=true;break;}if(rc==AVERROR_EOF){reason="no_frame_eof";break;}if(rc!=AVERROR(EAGAIN)){reason="receive_"+std::to_string(rc);break;}
   if(drainSent){std::this_thread::sleep_for(std::chrono::milliseconds(2));continue;}
   if(!pending&&!draining){do{av_packet_unref(pkt);rc=av_read_frame(fmt,pkt);}while(rc>=0&&pkt->stream_index!=stream);if(rc<0){if(rc!=AVERROR_EOF){reason="read_"+std::to_string(rc);break;}draining=true;}else pending=true;}
   rc=tl.query(101,[&]{return avcodec_send_packet(dec,draining?nullptr:pkt);});if(rc==0){pending=false;if(draining)drainSent=true;av_packet_unref(pkt);}else if(rc!=AVERROR(EAGAIN)&&rc!=AVERROR_EOF){reason="send_"+std::to_string(rc);break;}
   if(draining&&rc==AVERROR_EOF)drainSent=true;
  }
  if(!success){if(reason=="not_started")reason=stopping?"stopped":"deadline";break;}
  if(hw&&frame->format!=AV_PIX_FMT_OHCODEC){success=false;reason="unexpected_hw_format";break;}
  auto*m=av_frame_get_side_data(frame,AV_FRAME_DATA_MASTERING_DISPLAY_METADATA);auto*c=av_frame_get_side_data(frame,AV_FRAME_DATA_CONTENT_LIGHT_LEVEL);auto data=p26::readMetadata(m?m->data:nullptr,m?m->size:0,c?c->data:nullptr,c?c->size:0);
  int sw=frame->hw_frames_ctx?((AVHWFramesContext*)frame->hw_frames_ctx->data)->sw_format:frame->format;
  std::ostringstream row;row<<"P26_FRAME {\"sample\":"<<jsonstr(sample)<<",\"decoder\":"<<jsonstr(codec->name)<<",\"pts\":"<<frame->pts<<",\"format\":"<<frame->format<<",\"swFormat\":"<<sw<<",\"primaries\":"<<frame->color_primaries<<",\"transfer\":"<<frame->color_trc<<",\"matrix\":"<<frame->colorspace<<",\"range\":"<<frame->color_range<<",\"mdmPresent\":"<<(data.mdm?"true":"false")<<",\"mdmSize\":"<<(m?m->size:0)<<",\"cllPresent\":"<<(data.cll?"true":"false")<<",\"cllSize\":"<<(c?c->size:0)<<",\"maxLuminance\":"<<data.maxLuminance<<",\"minLuminance\":"<<data.minLuminance<<",\"maxCLL\":"<<data.maxCLL<<",\"maxFALL\":"<<data.maxFALL<<"}";log(f,row.str());
  if(m&&m->size>=sizeof(AVMasteringDisplayMetadata)){auto*raw=(AVMasteringDisplayMetadata*)m->data;auto rational=[](AVRational q){return "["+std::to_string(q.num)+","+std::to_string(q.den)+"]";};std::string prim="[";for(int x=0;x<3;x++){if(x)prim+=",";prim+="["+rational(raw->display_primaries[x][0])+","+rational(raw->display_primaries[x][1])+"]";}prim+="]";log(f,"P26_MDM_RAW {\"hasPrimaries\":"+std::to_string(raw->has_primaries)+",\"hasLuminance\":"+std::to_string(raw->has_luminance)+",\"primaries\":"+prim+",\"whitePoint\":["+rational(raw->white_point[0])+","+rational(raw->white_point[1])+"],\"minLuminance\":"+rational(raw->min_luminance)+",\"maxLuminance\":"+rational(raw->max_luminance)+"}");}
  if(hw){
   if(!frame->data[3]){reason="missing_token";success=false;break;}rc=av_ohcodec_release_buffer((AVOHCodecBuffer*)frame->data[3],1);log(f,"P26_RENDER rc="+std::to_string(rc));if(rc){reason="render";success=false;break;}
   if(!notify->wait(5000)){reason="frame_callback_timeout";success=false;break;}
   OHNativeWindowBuffer*wb=nullptr;int fence=-1;rc=OH_NativeImage_AcquireNativeWindowBuffer(image,&wb,&fence);log(f,"P26_ACQUIRE rc="+std::to_string(rc)+" buffer="+std::to_string(wb!=nullptr));if(rc||!wb){reason="acquire";success=false;break;}
   int ref=OH_NativeWindow_NativeObjectReference(wb);OH_NativeBuffer*nb=nullptr;int convert=ref?ref:OH_NativeBuffer_FromNativeWindowBuffer(wb,&nb);
   if(!convert&&nb){OH_NativeBuffer_Config cfg{};OH_NativeBuffer_GetConfig(nb,&cfg);OH_NativeBuffer_ColorSpace cs{};int color=OH_NativeBuffer_GetColorSpace(nb,&cs);bool p010=cfg.format==NATIVEBUFFER_PIXEL_FMT_YCBCR_P010||cfg.format==NATIVEBUFFER_PIXEL_FMT_YCRCB_P010;
    log(f,"P26_BUFFER {\"framePTS\":"+std::to_string(frame->pts)+",\"acquireIndex\":0,\"sequence\":"+std::to_string(OH_NativeBuffer_GetSeqNum(nb))+",\"width\":"+std::to_string(cfg.width)+",\"height\":"+std::to_string(cfg.height)+",\"stride\":"+std::to_string(cfg.stride)+",\"format\":"+std::to_string(cfg.format)+",\"usage\":"+std::to_string(cfg.usage)+",\"p010\":"+(p010?"true":"false")+",\"colorRC\":"+std::to_string(color)+",\"colorSpace\":"+std::to_string(cs)+"}");
   }else{success=false;reason="buffer_convert_"+std::to_string(convert);}
   if(j.mode=="direct-flush"){log(f,"P27_INTERVENTION op=flush-begin t="+std::to_string(mono()));avcodec_flush_buffers(dec);log(f,"P27_INTERVENTION op=flush-end t="+std::to_string(mono()));}
   if(j.mode=="direct-close"){log(f,"P27_INTERVENTION op=close-begin t="+std::to_string(mono()));avcodec_free_context(&dec);log(f,"P27_INTERVENTION op=close-end t="+std::to_string(mono()));}
   int release=p26::returnBuffer(image,wb,fence,ref==0,p26Release,p26Unref);log(f,"P26_RELEASE rc="+std::to_string(release));if(release){success=false;reason="buffer_release";}
  }
  if(success)reason="first_frame_observed";
 }while(false);
 cleanup();
}
static void execute(napi_env env,void*data){auto&j=*(Job*)data;if(j.mode.rfind("direct-",0)==0)execute_direct(j);else execute_mpv(env,data);}
