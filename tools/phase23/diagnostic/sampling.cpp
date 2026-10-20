#include <mpv/client.h>
int p22_sample_video(mpv_handle *p,double *pts){int interlaced=0;int rc=mpv_get_property(p,"video-frame-info/interlaced",MPV_FORMAT_FLAG,&interlaced);if(rc<0)return rc;return mpv_get_property(p,"time-pos",MPV_FORMAT_DOUBLE,pts);}
