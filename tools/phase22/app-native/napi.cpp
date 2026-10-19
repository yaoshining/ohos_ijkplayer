#include <napi/native_api.h>
#include <hilog/log.h>
#include <mpv/client.h>
#include "play_factory.h"
#include "expected.h"
#include "smb_probe.h"
#include "resource_case.h"
#include <dirent.h>
#include <native_window/external_window.h>
#include <native_buffer/buffer_common.h>
extern "C" {
#include "integration.h"
#include <libavformat/ohcodec_smb_runtime.h>
#include <libavutil/sha.h>
#include <libavutil/mem.h>
int p22_surface_valid(const char*,int,int);
}
#include <atomic>
#include <fstream>
#include <sstream>
#include <string>
#include <vector>
#include <chrono>
#include <sys/stat.h>
#include <unistd.h>
#include <errno.h>
#include <cmath>
extern int p22_sample_video(mpv_handle*,double*);
static std::atomic<bool> busy{false},stopping{false};
struct Job {napi_async_work work; napi_deferred deferred;std::string root,surface,mode,result;int width,height;};
static std::string hashfile(const std::string &p){std::ifstream f(p,std::ios::binary);if(!f)return "unreadable";AVSHA *s=av_sha_alloc();av_sha_init(s,256);char buf[65536];while(f){f.read(buf,sizeof(buf));av_sha_update(s,(uint8_t*)buf,f.gcount());}uint8_t sum[32];av_sha_final(s,sum);av_free(s);char h[65];for(int i=0;i<32;i++)sprintf(h+i*2,"%02x",sum[i]);return h;}
static void log(std::ofstream &f,const std::string &s){f<<s<<'\n';f.flush();OH_LOG_Print(LOG_APP,LOG_INFO,0x2255,"Phase22","%{public}s",s.c_str());}
static bool maps(const std::string &root,std::ofstream &f){
 std::ifstream in("/proc/self/maps");std::ofstream out(root+"/maps.txt");if(!in||!out)return false;std::string line;std::map<std::string,std::string> seen;
 while(std::getline(in,line)){out<<line<<'\n';auto pos=line.find('/');if(pos==std::string::npos)continue;std::string path=line.substr(pos),name=path.substr(path.find_last_of('/')+1);auto wanted=expected.find(name);if(wanted==expected.end())continue;if(seen.count(name))continue;std::string h=hashfile(path);seen[name]=h;log(f,"loaded "+path+" sha256="+h);}
 bool okay=seen==expected;log(f,"mapped_expected_libraries="+std::to_string(seen.size())+" all_sha_match="+std::to_string(okay));return okay;
}
static int countdir(const char *path){DIR*d=opendir(path);if(!d)return -1;int n=0;while(auto*e=readdir(d))if(e->d_name[0]!='.')n++;closedir(d);return n;}
static std::string fdtypes(){std::map<std::string,int> types;DIR*d=opendir("/proc/self/fd");if(!d)return "unavailable";while(auto*e=readdir(d)){if(e->d_name[0]=='.')continue;char b[4096];auto path=std::string("/proc/self/fd/")+e->d_name;auto n=readlink(path.c_str(),b,sizeof(b)-1);if(n<0)continue;b[n]=0;std::string key=b;if(key.rfind("socket:",0)==0)key="socket";if(key.rfind("pipe:",0)==0)key="pipe";types[key]++;}closedir(d);std::string out;for(auto &t:types)out+=t.first+"="+std::to_string(t.second)+";";return out;}
static std::string usage(){std::ifstream f("/proc/self/status");std::string s,r;while(std::getline(f,s))if(s.rfind("VmRSS:",0)==0||s.rfind("Threads:",0)==0)r+=s+" ";return "fd="+std::to_string(countdir("/proc/self/fd"))+" tasks="+std::to_string(countdir("/proc/self/task"))+" "+r;}
static std::string prop(mpv_handle *p,const char *n){char *s=mpv_get_property_string(p,n);std::string r=s?s:"unavailable";mpv_free(s);return r;}
static void execute(napi_env,void *data){Job &j=*(Job*)data;std::ofstream f(j.root+"/"+j.mode+".log");log(f,"case="+j.mode+" surface="+j.surface);log(f,"resources_before "+usage());
 std::string conf=j.root+"/smb.conf",state=j.root+"/state",cache=j.root+"/cache",resources=j.root+"/resources";
 struct p21_config c={conf.c_str(),state.c_str(),cache.c_str(),resources.c_str()};struct p21_error e;mpv_handle *p=nullptr;OHNativeWindow *window=nullptr;int oldFormat=-1;
 auto finish=[&](const std::string &r){if(p){mpv_terminate_destroy(p);p=nullptr;}if(window){if(oldFormat>=0)OH_NativeWindow_NativeWindowHandleOpt(window,SET_FORMAT,oldFormat);OH_NativeWindow_DestroyNativeWindow(window);window=nullptr;}log(f,"resources_after "+usage());log(f,"fd_types "+fdtypes());log(f,"result "+r);j.result=r;};
 if(j.mode=="init"||j.mode=="repeat"||j.mode=="conflict"){
  int rc=p21_create(&c,&p,&e);log(f,"create stage="+std::string(e.stage)+" code="+std::to_string(e.code));bool mapped=maps(j.root,f);
  if(rc<0||!mapped){finish("failed initialization or maps");return;}
  if(j.mode=="repeat"){p21_destroy(&p);p21_destroy(&p);rc=p21_create(&c,&p,&e);log(f,"repeat code="+std::to_string(e.code));}
  if(j.mode=="conflict"){std::string other=j.root+"/other.conf";c.config_file=other.c_str();mpv_handle *q=nullptr;rc=p21_create(&c,&q,&e);if(q)p21_destroy(&q);log(f,"conflict stage="+std::string(e.stage)+" code="+std::to_string(e.code));rc=rc<0&&std::string(e.stage)=="samba"&&e.code==EBUSY?0:-1;}
  finish(rc==0?"passed initialization":"failed initialization");return;
 }
 if(j.mode=="resource-negatives"){
  bool okay=maps(j.root,f);std::string before=hashfile(resources+"/fonts/font1.ttf");
  for(auto mode:{"missing-font","bad-font","font-permission","cache-permission","missing-cache-directory","font-symlink"}){
   bool rc=p22_resource_case(j.root,mode,[&](){mpv_handle *q=nullptr;int rc=p21_create(&c,&q,&e);if(q)p21_destroy(&q);return rc<0&&std::string(e.stage)=="resources"?e.code:0;},[&](const std::string &s){log(f,s);});okay=rc&&okay;
  }
  okay=okay&&hashfile(resources+"/fonts/font1.ttf")==before&&p21_validate(&c,&e)==0;finish(okay?"passed six resource negatives and restored":"failed resource negatives");return;
 }
 if(j.mode=="smb-read") {int rc=p21_create(&c,&p,&e);if(rc||!maps(j.root,f)){finish("failed SMB preparation");return;}p21_destroy(&p);finish(p22_smb_read(j.root,[&](const std::string &s){log(f,s);}));return;}
 bool vk=j.mode.rfind("vk-",0)==0,gl=j.mode.rfind("gl-",0)==0,hevc=j.mode.find("hevc")!=std::string::npos,hw=j.mode.find("sw")==std::string::npos;
 if(!(j.mode=="vk-missing"||j.mode=="gl-window-rgba8-sw"||j.mode=="gl-window-rgba8-h264"||j.mode=="gl-rgba8-sw"||j.mode=="gl-rgba8-h264"||j.mode=="gl-sw"||j.mode=="gl-h264"||j.mode=="gl-hevc"||j.mode=="vk-h264"||j.mode=="vk-hevc")||!p22_surface_valid(j.surface.c_str(),j.width,j.height)){finish("unsupported mode or invalid surface");return;}
 if(p21_validate(&c,&e)){finish("failed resources "+std::to_string(e.code));return;}
 struct ohcodec_smb_runtime_v1 config={sizeof(config),c.config_file,c.state_root,c.cache_root,c.resource_root};if(ohcodec_smb_runtime_configure_v1(&config)){finish("failed samba "+std::to_string(errno));return;}
 std::string fonts=resources+"/cjk",demux=cache+"/demux";
 if(hashfile(fonts+"/Mplus1p-Regular.ttf")!="ebbb56c23c64e512e2c1e8ccebca40347df7f93195438925e214b026c06b7117"){finish("failed CJK font SHA");return;}
 if(j.mode.find("window-rgba8")!=std::string::npos){int create=OH_NativeWindow_CreateNativeWindowFromSurfaceId(std::stoull(j.surface),&window);int get=window?OH_NativeWindow_NativeWindowHandleOpt(window,GET_FORMAT,&oldFormat):-1;int set=window?OH_NativeWindow_NativeWindowHandleOpt(window,SET_FORMAT,NATIVEBUFFER_PIXEL_FMT_RGBA_8888):-1;log(f,"native_window_rgba8 create="+std::to_string(create)+" get="+std::to_string(get)+" old="+std::to_string(oldFormat)+" set="+std::to_string(set)+" requested="+std::to_string(NATIVEBUFFER_PIXEL_FMT_RGBA_8888));if(create||get||set){finish("blocked native window RGBA8");return;}}
 p22_play_config pc={j.surface.c_str(),j.width,j.height,vk,hw,fonts.c_str(),demux.c_str(),j.mode.find("rgba8")!=std::string::npos};int rc=p22_play_create(&pc,&p);if(rc<0){finish("play factory failed "+std::string(mpv_error_string(rc)));return;}
 mpv_request_log_messages(p,"v");if(!maps(j.root,f)){finish("failed maps");return;}
 std::string file=j.root+(j.mode=="vk-missing"?"/definitely-missing-phase22.mp4":hevc?"/hevc.mp4":"/h264.mp4");const char *load[]={"loadfile",file.c_str(),nullptr};if(mpv_command(p,load)<0){finish("load failed");return;}
 bool loaded=false,eof=false,seeked=false;int frames=0,driftSamples=0;bool seekRestart=false,seekPTS=false;double last=-1,maxDrift=-1;std::string hwactual="unavailable",ao="unavailable",gpu="unavailable";auto start=std::chrono::steady_clock::now();
 while(!stopping&&std::chrono::steady_clock::now()-start<std::chrono::seconds(25)){
  mpv_event *event=mpv_wait_event(p,.05);
  if(event->event_id==MPV_EVENT_LOG_MESSAGE){auto *m=(mpv_event_log_message*)event->data;log(f,std::string(m->prefix)+"/"+m->level+" "+m->text);}
  if(event->event_id==MPV_EVENT_FILE_LOADED){loaded=true;log(f,"FILE_LOADED");std::string sub=j.root+"/subtitle.ass";const char *s[]={"sub-add",sub.c_str(),"select",nullptr};mpv_command(p,s);const char *osd[]={"show-text","OSD 中文字幕","20000",nullptr};mpv_command(p,osd);}
  if(event->event_id==MPV_EVENT_PLAYBACK_RESTART){log(f,"PLAYBACK_RESTART");if(seeked)seekRestart=true;}
  if(event->event_id==MPV_EVENT_END_FILE){auto *e=(mpv_event_end_file*)event->data;log(f,"END_FILE reason="+std::to_string(e->reason)+" error="+std::to_string(e->error));eof=e->reason==MPV_END_FILE_REASON_EOF;break;}
  double pts=0,drift=0;if(p22_sample_video(p,&pts)==0&&pts!=last){last=pts;frames++;log(f,"frame_present_playback_pts="+std::to_string(pts));}
  if(mpv_get_property(p,"avsync",MPV_FORMAT_DOUBLE,&drift)==0){if(std::isfinite(drift)){maxDrift=std::max(maxDrift,std::abs(drift));driftSamples++;}}
  if(seekRestart&&!seekPTS&&last>=4.9&&last<6.0){seekPTS=true;log(f,"seek_confirmed_pts="+std::to_string(last));}
  if(loaded){auto v=prop(p,"hwdec-current");if(v!="unavailable")hwactual=v;v=prop(p,"current-ao");if(v!="unavailable")ao=v;v=prop(p,"current-gpu-context");if(v!="unavailable")gpu=v;}
  if(loaded&&!seeked&&last>3){const char *seek[]={"seek","5","absolute+exact",nullptr};int s=mpv_command(p,seek);log(f,"seek_return="+std::to_string(s));seeked=true;}
 }
 std::ostringstream result;result<<"loaded="<<loaded<<" eof="<<eof<<" observedDistinctPlaybackPTSWithFrame="<<frames<<" hwdec="<<hwactual<<" ao="<<ao<<" gpu="<<gpu<<" maxLogicalDrift="<<maxDrift<<" driftSamples="<<driftSamples<<" seekConfirmed="<<seekPTS<<" stopped="<<stopping;
 finish(result.str());
}
static void complete(napi_env env,napi_status status,void *data){auto *j=(Job*)data;napi_value s;napi_create_string_utf8(env,j->result.c_str(),NAPI_AUTO_LENGTH,&s);auto deferred=j->deferred;napi_delete_async_work(env,j->work);delete j;busy=false;napi_resolve_deferred(env,deferred,s);}
static std::string str(napi_env env,napi_value v){size_t n=0;napi_get_value_string_utf8(env,v,nullptr,0,&n);std::vector<char>b(n+1);napi_get_value_string_utf8(env,v,b.data(),b.size(),&n);return b.data();}
static napi_value run(napi_env env,napi_callback_info info){size_t n=5;napi_value a[5];napi_get_cb_info(env,info,&n,a,nullptr,nullptr);if(n!=5||busy.exchange(true)){napi_throw_error(env,nullptr,"invalid arguments or busy");return nullptr;}stopping=false;auto *j=new Job;j->root=str(env,a[0]);j->surface=str(env,a[1]);napi_get_value_int32(env,a[2],&j->width);napi_get_value_int32(env,a[3],&j->height);j->mode=str(env,a[4]);napi_value promise,name;napi_create_promise(env,&j->deferred,&promise);napi_create_string_utf8(env,"Phase22",NAPI_AUTO_LENGTH,&name);napi_create_async_work(env,nullptr,name,execute,complete,j,&j->work);napi_queue_async_work(env,j->work);return promise;}
static napi_value stop(napi_env env,napi_callback_info){stopping=true;napi_value v;napi_get_undefined(env,&v);return v;}
static napi_value init(napi_env env,napi_value exports){napi_property_descriptor d[]={{"run",nullptr,run,nullptr,nullptr,nullptr,napi_default,nullptr},{"stop",nullptr,stop,nullptr,nullptr,nullptr,napi_default,nullptr}};napi_define_properties(env,exports,2,d);return exports;}
static napi_module module={1,0,nullptr,init,"phase22",nullptr,{0}};
extern "C" __attribute__((constructor)) void Register(){napi_module_register(&module);}
