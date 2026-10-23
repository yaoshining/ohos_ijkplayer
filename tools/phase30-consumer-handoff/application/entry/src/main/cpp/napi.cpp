#include <napi/native_api.h>
#include "terminal_adapter.h"
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
#include <memory>
#include "phase25_mpv.h"
static std::shared_ptr<p25::Session> timeline;
static p25::State lifecycle;
static unsigned stageGeneration=0,deadStage=0;
#include <fstream>
#include <sstream>
#include <string>
#include <vector>
#include <chrono>
#include <sys/stat.h>
#include <unistd.h>
#include <errno.h>
#include <cmath>
#include <thread>
#include <sys/types.h>
extern int p22_sample_video(mpv_handle*,double*);
static std::atomic<bool> busy{false},stopping{false};
static std::atomic<unsigned> sequence{0};
struct Job {napi_async_work work; napi_deferred deferred;std::string root,surface,mode,result;int width,height;unsigned sequence;std::shared_ptr<p25::Session> timeline;};
static std::string hashfile(const std::string &p){std::ifstream f(p,std::ios::binary);if(!f)return "unreadable";AVSHA *s=av_sha_alloc();av_sha_init(s,256);char buf[65536];while(f){f.read(buf,sizeof(buf));av_sha_update(s,(uint8_t*)buf,f.gcount());}uint8_t sum[32];av_sha_final(s,sum);av_free(s);char h[65];for(int i=0;i<32;i++)sprintf(h+i*2,"%02x",sum[i]);return h;}
static void log(std::ofstream &f,const std::string &s){f<<s<<'\n';f.flush();if(!f&&p25::workerSession)p25::workerSession->noteError();OH_LOG_Print(LOG_APP,LOG_INFO,0x2255,"Phase22","%{public}s",s.c_str());}
static bool maps(const std::string &root,std::ofstream &f){
 std::ifstream in("/proc/self/maps");std::ofstream out(root+"/maps.txt");if(!in||!out)return false;std::string line;std::map<std::string,std::string> seen;
 while(std::getline(in,line)){out<<line<<'\n';auto pos=line.find('/');if(pos==std::string::npos)continue;std::string path=line.substr(pos),name=path.substr(path.find_last_of('/')+1);auto wanted=expected.find(name);if(wanted==expected.end())continue;if(seen.count(name))continue;std::string h=hashfile(path);seen[name]=h;log(f,"loaded "+path+" sha256="+h);}
 bool okay=seen==expected;log(f,"mapped_expected_libraries="+std::to_string(seen.size())+" all_sha_match="+std::to_string(okay));return okay;
}
static int countdir(const char *path){DIR*d=opendir(path);if(!d)return -1;int n=0;while(auto*e=readdir(d))if(e->d_name[0]!='.')n++;closedir(d);return n;}
static std::string fdtypes(){std::map<std::string,int> types;DIR*d=opendir("/proc/self/fd");if(!d)return "unavailable";while(auto*e=readdir(d)){if(e->d_name[0]=='.')continue;char b[4096];auto path=std::string("/proc/self/fd/")+e->d_name;auto n=readlink(path.c_str(),b,sizeof(b)-1);if(n<0)continue;b[n]=0;std::string key=b;if(key.rfind("socket:",0)==0)key="socket";if(key.rfind("pipe:",0)==0)key="pipe";types[key]++;}closedir(d);std::string out;for(auto &t:types)out+=t.first+"="+std::to_string(t.second)+";";return out;}
static std::string usage(){std::ifstream f("/proc/self/status");std::string s,r;while(std::getline(f,s))if(s.rfind("VmRSS:",0)==0||s.rfind("Threads:",0)==0)r+=s+" ";return "fd="+std::to_string(countdir("/proc/self/fd"))+" tasks="+std::to_string(countdir("/proc/self/task"))+" "+r;}
static std::string prop(mpv_handle *p,const char *n){char *s=nullptr;int rc=p25::get(p,n,MPV_FORMAT_STRING,&s);std::string r=rc>=0&&s?s:"unavailable";mpv_free(s);return r;}
static void snapshot(std::ofstream &f,const std::string &stage){
 log(f,"P23_SAMPLE stage="+stage+" "+usage());
 DIR*d=opendir("/proc/self/fd");if(!d){log(f,"P23_FD_ERROR stage="+stage);return;}
 int own=dirfd(d);while(auto*e=readdir(d)){
  if(e->d_name[0]=='.')continue;int fd=atoi(e->d_name);if(fd==own)continue;
  char b[4096];std::string path=std::string("/proc/self/fd/")+e->d_name;auto n=readlink(path.c_str(),b,sizeof(b)-1);if(n<0)continue;b[n]=0;
  struct stat st{};int rc=fstat(fd,&st);log(f,"P23_FD stage="+stage+" fd="+std::to_string(fd)+" ino="+std::to_string(st.st_ino)+" dev="+std::to_string(st.st_dev)+" stat_rc="+std::to_string(rc)+" target="+b);
  if(std::string(b).find("dmabuf")!=std::string::npos||std::string(b).find("ashmem")!=std::string::npos){
   std::ifstream info(std::string("/proc/self/fdinfo/")+e->d_name);std::string line;bool available=info.is_open();int fields=0;
   while(std::getline(info,line)){auto colon=line.find(':');std::string key=line.substr(0,colon);if(key=="size"||key=="count"||key=="exp_name"||key=="name"||key=="ino"||key=="flags"||key=="mnt_id"){log(f,"P23_FDINFO stage="+stage+" fd="+std::to_string(fd)+" "+line);fields++;}}
   log(f,"P23_FDINFO_STATUS stage="+stage+" fd="+std::to_string(fd)+" readable="+std::to_string(available)+" fields="+std::to_string(fields));
  }
 }closedir(d);
}
static void window_format(std::ofstream &f,const std::string &id,const std::string &stage){
 OHNativeWindow *w=nullptr;int create=OH_NativeWindow_CreateNativeWindowFromSurfaceId(std::stoull(id),&w);int fmt=-1;int rc=w?OH_NativeWindow_NativeWindowHandleOpt(w,GET_FORMAT,&fmt):-1;
 int width=-1,height=-1;int geometry=w?OH_NativeWindow_NativeWindowHandleOpt(w,GET_BUFFER_GEOMETRY,&height,&width):-1;
 log(f,"P23_GEOMETRY stage="+stage+" rc="+std::to_string(geometry)+" width="+std::to_string(width)+" height="+std::to_string(height));
 log(f,"P23_WINDOW stage="+stage+" create="+std::to_string(create)+" get="+std::to_string(rc)+" format="+std::to_string(fmt));if(w)OH_NativeWindow_DestroyNativeWindow(w);
}
#include "phase25_runner.inc"
#include "hdr_direct.inc"
static void complete(napi_env env,napi_status status,void *data){auto *j=(Job*)data;napi_value s;napi_create_string_utf8(env,j->result.c_str(),NAPI_AUTO_LENGTH,&s);auto deferred=j->deferred;napi_delete_async_work(env,j->work);delete j;busy=false;napi_resolve_deferred(env,deferred,s);}
static std::string str(napi_env env,napi_value v){size_t n=0;napi_get_value_string_utf8(env,v,nullptr,0,&n);std::vector<char>b(n+1);napi_get_value_string_utf8(env,v,b.data(),b.size(),&n);return b.data();}
static napi_value run(napi_env env,napi_callback_info info){if(!terminal_app_admit()){napi_throw_error(env,nullptr,"terminal capability missing or process terminal; playback/fallback refused");return nullptr;}size_t n=5;napi_value a[5];napi_get_cb_info(env,info,&n,a,nullptr,nullptr);if(n!=5||busy.exchange(true)){napi_throw_error(env,nullptr,"invalid arguments or busy");return nullptr;}if(!timeline){busy=false;napi_throw_error(env,nullptr,"timeline unavailable");return nullptr;}stopping=false;auto *j=new Job;j->timeline=timeline;j->sequence=sequence++;j->root=str(env,a[0]);j->surface=str(env,a[1]);napi_get_value_int32(env,a[2],&j->width);napi_get_value_int32(env,a[3],&j->height);j->mode=str(env,a[4]);if(j->mode=="callback-hang"||j->mode=="ui-block"||j->mode=="logger-hang")j->mode="vk-inject-wait";napi_value promise,name;napi_create_promise(env,&j->deferred,&promise);napi_create_string_utf8(env,"Phase22",NAPI_AUTO_LENGTH,&name);napi_create_async_work(env,nullptr,name,execute,complete,j,&j->work);napi_queue_async_work(env,j->work);return promise;}
static napi_value stop(napi_env env,napi_callback_info){if(!terminal_app_state())stopping=true;napi_value v;napi_get_undefined(env,&v);return v;}
static napi_value beginTimeline(napi_env env,napi_callback_info info){size_t n=1;napi_value a[1];napi_get_cb_info(env,info,&n,a,nullptr,nullptr);if(n!=1||timeline){napi_throw_error(env,nullptr,"timeline already initialized");return nullptr;}lifecycle=p25::State();stageGeneration=deadStage=0;timeline=std::make_shared<p25::Session>(str(env,a[0]));napi_value v;napi_get_boolean(env,timeline->errors()==0,&v);return v;}
static napi_value eventTimeline(napi_env env,napi_callback_info info){size_t n=3;napi_value a[3];napi_get_cb_info(env,info,&n,a,nullptr,nullptr);int32_t e=0,g=0,key=0;if(n!=3||!timeline){napi_value v;napi_get_boolean(env,false,&v);return v;}napi_get_value_int32(env,a[0],&e);napi_get_value_int32(env,a[1],&g);napi_get_value_int32(env,a[2],&key);
 bool okay=((e>=8&&e<=26)||(e>=29&&e<=32))&&g>=0&&key>=0;auto ev=static_cast<p25::Event>(e);
 if(okay&&(e>=12&&e<=19)){if(ev==p25::Event::StageCreate){okay=unsigned(g)>deadStage; if(okay)stageGeneration=g;}else okay=unsigned(g)==stageGeneration&&unsigned(g)>deadStage;if(okay&&ev==p25::Event::StageDestroy)deadStage=g;}
 if(okay)okay=lifecycle.apply(ev,g);if(okay&&ev==p25::Event::AbilityBackground)timeline->backgroundSeen=true;
 timeline->emit(p25::Lane::UI,okay?ev:p25::Event::Late,key,g);napi_value v;napi_get_boolean(env,okay,&v);return v;}
static napi_value closeTimeline(napi_env env,napi_callback_info){bool okay=!busy&&bool(timeline);if(okay){timeline->close();timeline.reset();}napi_value v;napi_get_boolean(env,okay,&v);return v;}
static napi_value configureTerminal(napi_env env,napi_callback_info info){size_t n=2;napi_value a[2];napi_get_cb_info(env,info,&n,a,nullptr,nullptr);bool ok=n==2&&terminal_app_start(str(env,a[0]).c_str(),str(env,a[1]).c_str());napi_value v;napi_get_boolean(env,ok,&v);return v;}
static napi_value terminalState(napi_env env,napi_callback_info){napi_value v;napi_create_int32(env,terminal_app_state(),&v);return v;}
static napi_value terminalMark(napi_env env,napi_callback_info info){size_t n=1;napi_value a[1];napi_get_cb_info(env,info,&n,a,nullptr,nullptr);int32_t code=0;if(n==1)napi_get_value_int32(env,a[0],&code);terminal_app_mark_ui(code);napi_value v;napi_get_undefined(env,&v);return v;}
static napi_value init(napi_env env,napi_value exports){napi_property_descriptor d[]={{"configureTerminal",nullptr,configureTerminal,nullptr,nullptr,nullptr,napi_default,nullptr},{"terminalState",nullptr,terminalState,nullptr,nullptr,nullptr,napi_default,nullptr},{"terminalMark",nullptr,terminalMark,nullptr,nullptr,nullptr,napi_default,nullptr},{"run",nullptr,run,nullptr,nullptr,nullptr,napi_default,nullptr},{"stop",nullptr,stop,nullptr,nullptr,nullptr,napi_default,nullptr},{"beginTimeline",nullptr,beginTimeline,nullptr,nullptr,nullptr,napi_default,nullptr},{"event",nullptr,eventTimeline,nullptr,nullptr,nullptr,napi_default,nullptr},{"closeTimeline",nullptr,closeTimeline,nullptr,nullptr,nullptr,napi_default,nullptr}};napi_define_properties(env,exports,8,d);return exports;}
static napi_module module={1,0,nullptr,init,"phase22",nullptr,{0}};
extern "C" __attribute__((constructor)) void Register(){napi_module_register(&module);}
