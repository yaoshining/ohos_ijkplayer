#include "play_factory.h"
#include <cassert>
#include <cstring>
#include <string>
struct mpv_handle {int x;};static mpv_handle handle;static bool quiet=false,rgb10=false;static int nodeOptions=0,init=0,destroyed=0,calls=0,fail=0;
extern "C" mpv_handle *mpv_create(){return &handle;}
extern "C" void mpv_terminate_destroy(mpv_handle*){destroyed++;}
extern "C" int mpv_set_option_string(mpv_handle*,const char*n,const char*v){calls++;assert(std::string(v).find("private-pass")==std::string::npos);if(!strcmp(n,"msg-level")&&!strcmp(v,"all=no"))quiet=true;if(!strcmp(n,"egl-output-format")&&!strcmp(v,"rgb10_a2"))rgb10=true;return calls==fail?-88:0;}
extern "C" int mpv_set_option(mpv_handle*,const char*n,mpv_format f,void*d){calls++;assert(quiet&&init==0);assert(f==MPV_FORMAT_NODE);auto*node=(mpv_node*)d;assert(node->format==MPV_FORMAT_NODE_MAP&&node->u.list->num==4);assert(!strcmp(node->u.list->keys[1],"password"));assert(!strcmp(node->u.list->values[1].u.string,"private-pass,:@"));nodeOptions++;return calls==fail?-88:0;}
extern "C" int mpv_initialize(mpv_handle*){init++;return 0;}
extern "C" int p22_surface_valid(const char*,int,int){return 1;}
int main(){p22_play_config c={"123",1920,1080,0,1,"/fonts","/cache",0,true,"u","private-pass,:@","D"};c.rgb10=true;
 for(int n=0;n<50;n++){quiet=rgb10=false;nodeOptions=init=destroyed=calls=0;fail=n;mpv_handle*p=nullptr;int r=p22_play_create(&c,&p);if(n>0&&n<=calls){assert(r<0&&!p&&destroyed==1&&init==0);}else{assert(!r&&p&&quiet&&rgb10&&nodeOptions==2&&init==1);mpv_terminate_destroy(p);}}
}
