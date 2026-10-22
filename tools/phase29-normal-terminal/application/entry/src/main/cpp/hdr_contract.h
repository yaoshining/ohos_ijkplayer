#pragma once
#include <cstddef>
#include <mutex>
#include <condition_variable>
#include <chrono>
#include <atomic>
#include <array>
extern "C" {
#include <libavutil/mastering_display_metadata.h>
}
namespace p26 {
// SDK does not specify a callback-drain barrier. Slots have process lifetime,
// never reuse identities, and are capped at 64 (fail closed after exhaustion).
class CallbackState {
 std::mutex mutex;std::condition_variable cv;bool live=true;unsigned count=0,lateCount=0;
public:
 bool signal(){std::lock_guard<std::mutex>l(mutex);if(!live){lateCount++;return false;}count++;cv.notify_all();return true;}
 bool wait(unsigned milliseconds){std::unique_lock<std::mutex>l(mutex);return cv.wait_for(l,std::chrono::milliseconds(milliseconds),[&]{return count>0||!live;})&&count>0;}
 void retire(){std::lock_guard<std::mutex>l(mutex);live=false;cv.notify_all();}
 unsigned late(){std::lock_guard<std::mutex>l(mutex);return lateCount;}
};
inline CallbackState* acquireCallbackState(){static auto*slots=new std::array<CallbackState,64>;static std::atomic<unsigned>next{0};auto i=next.fetch_add(1);return i<64?&(*slots)[i]:nullptr;}

struct Metadata {bool mdm=false,cll=false; double maxLuminance=0,minLuminance=0; unsigned maxCLL=0,maxFALL=0;};
inline Metadata readMetadata(const void*m,size_t ms,const void*c,size_t cs){
 Metadata o;
 if(m&&ms>=sizeof(AVMasteringDisplayMetadata)){const auto&v=*(const AVMasteringDisplayMetadata*)m;if(v.has_luminance&&v.max_luminance.den>0&&v.min_luminance.den>0){o.mdm=true;o.maxLuminance=double(v.max_luminance.num)/v.max_luminance.den;o.minLuminance=double(v.min_luminance.num)/v.min_luminance.den;}}
 if(c&&cs>=sizeof(AVContentLightMetadata)){const auto&v=*(const AVContentLightMetadata*)c;o.cll=true;o.maxCLL=v.MaxCLL;o.maxFALL=v.MaxFALL;}return o;
}
// SDK consumes fence even on release failure. Successful queue return consumes
// acquired wrapper; failure retains it. Drop the explicit extra ref last.
inline int returnBuffer(void*image,void*buffer,int fence,bool extra,int(*release)(void*,void*,int),int(*unref)(void*)){
 int rc=release(image,buffer,fence);if(rc)unref(buffer);if(extra)unref(buffer);return rc;
}
}
