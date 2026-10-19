#include "play_factory.h"
#include <string>
#include <vector>
extern "C" int p22_surface_valid(const char*,int,int);
int p22_play_create(const p22_play_config *c,mpv_handle **out){
 if(!out)return -1;*out=nullptr;if(!c||!c->fonts||!c->cache||!p22_surface_valid(c->surface,c->width,c->height))return -1;
 mpv_handle *p=mpv_create();if(!p)return -1;
 std::string size=std::to_string(c->width)+"x"+std::to_string(c->height);
 std::vector<std::pair<std::string,std::string>> opts={{"config","no"},{"load-scripts","no"},{"sub-auto","no"},{"embeddedfonts","no"},{"sub-font-provider","none"},{"osd-font-provider","none"},{"sub-fonts-dir",c->fonts},{"osd-fonts-dir",c->fonts},{"sub-font","Mplus 1p"},{"osd-font","Mplus 1p"},{"demuxer-cache-dir",c->cache},{"vo","gpu-next"},{"gpu-api",c->vulkan?"vulkan":"opengl"},{"gpu-context",c->vulkan?"ohosvk":"ohos"},{"wid",c->surface},{"ohos-surface-size",size},{"ao","ohaudio"},{"hwdec",c->hardware?"ohcodec":"no"},{"hwdec-software-fallback","no"},{"idle","yes"},{"keep-open","no"},{"pause","no"},{"terminal","no"},{"osd-level","0"},{"sub-ass-override","force"},{"sub-font-size","32"},{"osd-font-size","32"}};
 if(c->rgba8){opts.push_back({"opengl-es","yes"});opts.push_back({"egl-output-format","rgba8"});}
 for(auto &o:opts){int rc=mpv_set_option_string(p,o.first.c_str(),o.second.c_str());if(rc<0){mpv_terminate_destroy(p);return rc;}}
 int rc=mpv_initialize(p);if(rc<0){mpv_terminate_destroy(p);return rc;}*out=p;return 0;
}
