#include "phase24_policy.h"
#include "phase24_metrics.h"
#include <iomanip>
#include <ctime>
static std::string jsonstr(const std::string&s){std::string o="\"";for(unsigned char c:s){if(c=='"'||c=='\\'){o+='\\';o+=c;}else if(c=='\n')o+="\\n";else if(c=='\r')o+="\\r";else if(c=='\t')o+="\\t";else if(c<32)o+='?';else o+=c;}return o+'"';}
static std::string jsonnode(const mpv_node &n){
 switch(n.format){case MPV_FORMAT_STRING:return jsonstr(n.u.string?n.u.string:"");case MPV_FORMAT_FLAG:return n.u.flag?"true":"false";case MPV_FORMAT_INT64:return std::to_string(n.u.int64);case MPV_FORMAT_DOUBLE:return std::isfinite(n.u.double_)?std::to_string(n.u.double_):"null";case MPV_FORMAT_NODE_ARRAY:case MPV_FORMAT_NODE_MAP:{std::string s=n.format==MPV_FORMAT_NODE_MAP?"{":"[";for(int i=0;i<n.u.list->num;i++){if(i)s+=",";if(n.format==MPV_FORMAT_NODE_MAP)s+=jsonstr(n.u.list->keys[i])+":";s+=jsonnode(n.u.list->values[i]);}return s+(n.format==MPV_FORMAT_NODE_MAP?"}":"]");}default:return "null";}
}
static double mono(){return std::chrono::duration<double>(std::chrono::steady_clock::now().time_since_epoch()).count();}

static bool private_fields(const std::string&path,std::vector<std::string>&a){std::ifstream f(path,std::ios::binary);for(int i=0;i<4;i++){unsigned char b[4];if(!f.read((char*)b,4))return false;uint32_t n=b[0]|(b[1]<<8)|(b[2]<<16)|(b[3]<<24);if(n>65536)return false;std::string s(n,'\0');if(!f.read(s.data(),n)||s.find('\0')!=std::string::npos)return false;a.push_back(s);}return f.peek()==EOF&&a[0].rfind("smb://",0)==0&&a[0].find('@')==std::string::npos;}
static void execute(napi_env,void*data){
 Job&j=*(Job*)data;std::ofstream f(j.root+"/"+j.mode+"-"+std::to_string(j.sequence)+".log");
 bool nas=j.mode.find("nas")!=std::string::npos,longRun=j.mode.find("long")!=std::string::npos,vk=j.mode.rfind("vk-",0)==0,hw=p24::hardwareForMode(j.mode),switching=j.mode.find("switch")!=std::string::npos;
 std::string sample=nas?"nas-media-01":j.mode.find("hlg")!=std::string::npos?"hlg":j.mode.find("sdr")!=std::string::npos?"sdr":"pq";
 mpv_handle*p=nullptr;p24::Continuity continuity;continuity.expectedGPU=vk?"ohosvk":"ohos";double began=mono();bool mapped=false,loaded=false,ended=false,seeked=false;int loadedCount=0,eofs=0,errors=0,ptsSamples=0;double lastPTS=-1;
 log(f,"P24_BEGIN case="+j.mode+" sample="+sample+" pid="+std::to_string(getpid())+" surface="+j.surface+" size="+std::to_string(j.width)+"x"+std::to_string(j.height)+" wallUnix="+std::to_string(time(nullptr))+" targetSeconds="+std::to_string(longRun?3600:12));
 auto finish=[&](const std::string&r){if(p){mpv_terminate_destroy(p);p=nullptr;}log(f,"P24_RESOURCE stage=destroyed "+usage());std::this_thread::sleep_for(std::chrono::seconds(3));log(f,"P24_RESOURCE stage=settled "+usage());log(f,"P24_RESULT "+r);j.result=r;};
 std::string conf=j.root+"/smb.conf",state=j.root+"/state",cache=j.root+"/cache",resources=j.root+"/resources";p21_config c={conf.c_str(),state.c_str(),cache.c_str(),resources.c_str()};p21_error e{};
 if(!p22_surface_valid(j.surface.c_str(),j.width,j.height)||p21_validate(&c,&e)){finish("failed_preflight code="+std::to_string(e.code));return;}
 ohcodec_smb_runtime_v1 config={sizeof(config),c.config_file,c.state_root,c.cache_root,c.resource_root};if(ohcodec_smb_runtime_configure_v1(&config)){finish("failed_runtime code="+std::to_string(errno));return;}
 std::vector<std::string>auth;if(nas&&!private_fields(j.root+"/nas.bin",auth)){finish("blocked_private_config");return;}
 std::string fonts=resources+"/cjk",demux=cache+"/demux";
 p22_play_config pc={j.surface.c_str(),j.width,j.height,vk,hw,fonts.c_str(),demux.c_str(),false,nas,nas?auth[1].c_str():nullptr,nas?auth[2].c_str():nullptr,nas?auth[3].c_str():nullptr};
 pc.rgb10=j.mode.find("rgb10")!=std::string::npos;
 int rc=p22_play_create(&pc,&p);if(rc<0){finish("failed_player code="+std::to_string(rc));return;}
 mpv_request_log_messages(p,nas?"no":"debug");mapped=maps(j.root,f);if(!mapped){finish("failed_maps");return;}
 std::vector<std::string>files=switching?std::vector<std::string>{"pq","sdr","pq","pq2","hlg","sdr"}:std::vector<std::string>{sample};size_t fileIndex=0;
 auto load=[&](){std::string path=nas?auth[0]:j.root+"/"+files[fileIndex]+"-bounded.mp4";log(f,"P24_LOAD sample="+(nas?sample:files[fileIndex])+" index="+std::to_string(fileIndex));if(!nas)log(f,"P24_INPUT sha256="+hashfile(path));const char*a[]={"loadfile",path.c_str(),nullptr};return mpv_command(p,a);};
 if(load()<0){finish("failed_load_command");return;}
 double next=0,nextResource=0;bool properties=false;double deadline=began+(longRun?3700:switching?110:nas?40:30);
 while(!stopping&&mono()<deadline){
  auto*ev=mpv_wait_event(p,.05);double now=mono(),elapsed=now-began;
  if(ev->event_id==MPV_EVENT_LOG_MESSAGE){auto*m=(mpv_event_log_message*)ev->data;auto s=p24::safe_mpv_log(nas,m->level,std::string(m->prefix)+" "+m->text);if(!s.empty())log(f,"P24_MPV "+s);}
  if(ev->event_id==MPV_EVENT_FILE_LOADED){loaded=true;loadedCount++;properties=false;log(f,"P24_FILE_LOADED index="+std::to_string(fileIndex));if(longRun&&loadedCount>1)continuity.interrupt("instance_reload");}
  if(ev->event_id==MPV_EVENT_SEEK){log(f,"P24_SEEK t="+std::to_string(elapsed));if(longRun)continuity.interrupt("seek");}
  if(ev->event_id==MPV_EVENT_PLAYBACK_RESTART){log(f,"P24_PLAYBACK_RESTART t="+std::to_string(elapsed));if(longRun)continuity.onRestart();}
  if(ev->event_id==MPV_EVENT_END_FILE){auto*x=(mpv_event_end_file*)ev->data;log(f,"P24_END reason="+std::to_string(x->reason)+" error="+std::to_string(x->error));if(x->reason==MPV_END_FILE_REASON_EOF)eofs++;else errors++;if(longRun){continuity.interrupt("early_end");ended=true;break;}if(switching&&x->reason==MPV_END_FILE_REASON_EOF&&++fileIndex<files.size()){loaded=false;lastPTS=-1;load();continue;}ended=true;break;}
  if(now>=nextResource){log(f,"P24_RESOURCE t="+std::to_string(elapsed)+" "+usage());nextResource=now+30;}
  if(now>=next){next=now+(nas?5:2);double pts=NAN,speed=NAN;int prc=p22_sample_video(p,&pts),src=mpv_get_property(p,"speed",MPV_FORMAT_DOUBLE,&speed),paused=0,cachePaused=0;int parc=mpv_get_property(p,"pause",MPV_FORMAT_FLAG,&paused),cprc=mpv_get_property(p,"paused-for-cache",MPV_FORMAT_FLAG,&cachePaused);
   auto actual=prop(p,"hwdec-current"),ao=prop(p,"current-ao"),gpu=prop(p,"current-gpu-context");std::string safeHW=actual=="ohcodec"?"ohcodec":actual=="no"?"no":"unavailable_or_other",safeAO=ao=="ohaudio"?"ohaudio":"unavailable_or_other",safeGPU=gpu=="ohos"||gpu=="ohosvk"?gpu:"unavailable_or_other";
   if(prc>=0&&std::isfinite(pts)&&pts!=lastPTS){ptsSamples++;lastPTS=pts;}
   std::string row="{\"t\":"+std::to_string(elapsed)+",\"wallUnix\":"+std::to_string(time(nullptr))+",\"fileIndex\":"+std::to_string(fileIndex)+",\"videoSampleRc\":"+std::to_string(prc)+",\"hwdec\":"+jsonstr(safeHW)+",\"ao\":"+jsonstr(safeAO)+",\"gpu\":"+jsonstr(safeGPU);
   for(auto*n:{"time-pos","duration","speed","avsync","estimated-vf-fps","frame-drop-count","decoder-frame-drop-count","cache-speed","demuxer-cache-duration","demuxer-cache-time","demuxer-cache-idle","cache-buffering-state","paused-for-cache","audio-pts","video-bitrate","audio-bitrate","packet-video-bitrate","packet-audio-bitrate","demuxer-start-time"})row+=","+p24metric(p,n);row+="}";log(f,"P24_OBSERVATION "+row);
   if(longRun&&loaded){bool valid=prc>=0&&src>=0&&parc>=0&&cprc>=0; if(continuity.start>=0||prc>=0)continuity.observe(elapsed,pts,speed,safeHW,paused||cachePaused,valid,safeGPU);if(!continuity.reason.empty())break;if(continuity.passed()){ended=true;break;}}
   if(loaded&&prc>=0&&!properties){properties=true;for(auto*n:{"video-dec-params","video-params","video-out-params","video-target-params","audio-params","audio-out-params"}){mpv_node node{};int q=mpv_get_property(p,n,MPV_FORMAT_NODE,&node);log(f,"P24_PARAMS name="+std::string(n)+" rc="+std::to_string(q)+" value="+(q>=0?jsonnode(node):"null"));mpv_free_node_contents(&node);}}
   if(nas&&!longRun&&loaded&&!seeked&&std::isfinite(pts)&&pts>10){const char*a[]={"seek","30","absolute+exact",nullptr};int q=mpv_command(p,a);log(f,"P24_SHORT_SEEK rc="+std::to_string(q));seeked=true;}
   if(nas&&!longRun&&seeked&&pts>40){ended=true;break;}
  }
 }
 if(stopping)continuity.interrupt("cancelled");if(!ended&&mono()>=deadline)continuity.interrupt("deadline");
 std::string result="loaded="+std::to_string(loadedCount)+" eof="+std::to_string(eofs)+" errors="+std::to_string(errors)+" distinctPtsSamples="+std::to_string(ptsSamples)+" wallElapsed="+std::to_string(mono()-began)+" continuousSeconds="+std::to_string(continuity.start>=0?continuity.last-continuity.start:0)+" continuousPassed="+std::to_string(longRun&&mapped&&continuity.passed())+" reason="+(continuity.reason.empty()?"none":continuity.reason)+" stopped="+std::to_string(stopping);
 finish(result);
}
