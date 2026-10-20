#include "phase25_mpv.h"
int p22_sample_video(mpv_handle *p,double *pts){int interlaced=0;int rc=p25::get(p,"video-frame-info/interlaced",MPV_FORMAT_FLAG,&interlaced);if(rc<0)return rc;return p25::get(p,"time-pos",MPV_FORMAT_DOUBLE,pts);}
