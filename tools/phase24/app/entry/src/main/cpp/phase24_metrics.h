#pragma once
#include <mpv/client.h>
#include <string>
#include <cmath>
#include <cstring>
inline std::string p24metric(mpv_handle*p,const char*name){
 bool flag=!strcmp(name,"paused-for-cache")||!strcmp(name,"demuxer-cache-idle");
 double v=NAN;int b=0;int rc=mpv_get_property(p,name,flag?MPV_FORMAT_FLAG:MPV_FORMAT_DOUBLE,flag?(void*)&b:(void*)&v);
 std::string value="null";if(rc>=0){if(flag)value=b?"true":"false";else if(std::isfinite(v))value=std::to_string(v);}
 return std::string("\"")+name+"\":{\"rc\":"+std::to_string(rc)+",\"value\":"+value+"}";
}
