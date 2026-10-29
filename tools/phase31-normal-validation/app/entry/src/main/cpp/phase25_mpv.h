#pragma once
#include "phase25_timeline.h"
#include <mpv/client.h>
#include <cstring>
namespace p25 {
// 固定索引；不输出任意属性名或返回字符串，诊断字段严格白名单。
inline unsigned propertyId(const char*n){static const char*names[]={"video-frame-info/interlaced","time-pos","speed","pause","paused-for-cache","hwdec-current","current-ao","current-gpu-context","duration","avsync","estimated-vf-fps","frame-drop-count","decoder-frame-drop-count","cache-speed","demuxer-cache-duration","demuxer-cache-time","demuxer-cache-idle","cache-buffering-state","audio-pts","video-bitrate","audio-bitrate","packet-video-bitrate","packet-audio-bitrate","demuxer-start-time","video-dec-params","video-params","video-out-params","video-target-params","audio-params","audio-out-params"};for(unsigned i=0;i<sizeof(names)/sizeof(*names);i++)if(!strcmp(n,names[i]))return i+1;return 0;}
inline thread_local Session* workerSession=nullptr;
inline int get(mpv_handle*p,const char*n,mpv_format f,void*v){auto key=propertyId(n);if(!key){if(workerSession)workerSession->noteError();return MPV_ERROR_INVALID_PARAMETER;}return workerSession?workerSession->query(key,[&]{return mpv_get_property(p,n,f,v);}):MPV_ERROR_UNINITIALIZED;}
}
