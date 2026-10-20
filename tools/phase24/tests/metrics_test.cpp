#include "phase24_metrics.h"
#include <cassert>
#include <cstring>
extern "C" int mpv_get_property(mpv_handle*,const char*n,mpv_format fmt,void*v){
 if(!strcmp(n,"paused-for-cache")||!strcmp(n,"demuxer-cache-idle")){if(fmt!=MPV_FORMAT_FLAG)return -9;*(int*)v=!strcmp(n,"demuxer-cache-idle");return 0;}
 if(!strcmp(n,"time-pos")){assert(fmt==MPV_FORMAT_DOUBLE);*(double*)v=20;return 0;}
 return -8;
}
int main(){auto p=(mpv_handle*)1;assert(p24metric(p,"paused-for-cache").find("\"value\":false")!=std::string::npos);assert(p24metric(p,"demuxer-cache-idle").find("\"value\":true")!=std::string::npos);assert(p24metric(p,"time-pos").find("20.000000")!=std::string::npos);assert(p24metric(p,"unknown").find("\"rc\":-8,\"value\":null")!=std::string::npos);}
