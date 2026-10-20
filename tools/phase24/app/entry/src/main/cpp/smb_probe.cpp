#include "smb_probe.h"
#include "seek_expected.h"
#include "safe_log.h"
#include "smb_options.h"
#include <sys/socket.h>
#include <arpa/inet.h>
#include <poll.h>
#include <fcntl.h>
#include <unistd.h>
extern "C" {
#include <libavformat/avformat.h>
#include <libavutil/sha.h>
#include <libavutil/mem.h>
#include <libavutil/log.h>
}
#include <fstream>
#include <vector>
#include <chrono>
static double now(){return std::chrono::duration<double>(std::chrono::steady_clock::now().time_since_epoch()).count();}
static int interrupt(void *p){return now()>*(double*)p;}
static std::function<void(const std::string&)> diagnostic;static std::vector<std::string> redact;
static void quiet(void*,int level,const char *fmt,va_list ap){if(level>AV_LOG_WARNING||!diagnostic)return;char b[4096];vsnprintf(b,sizeof(b),fmt,ap);diagnostic("ffmpeg_smb: "+p22_redact(b,redact));}
static std::string hash(const std::vector<uint8_t> &v){AVSHA *s=av_sha_alloc();av_sha_init(s,256);av_sha_update(s,v.data(),v.size());uint8_t d[32];av_sha_final(s,d);av_free(s);char b[65];for(int i=0;i<32;i++)sprintf(b+2*i,"%02x",d[i]);return b;}
std::string p22_smb_read(const std::string &root,std::function<void(const std::string&)> log){
 std::ifstream good(root+"/smb-test.txt"),bad(root+"/smb-wrong.txt");std::string url,wrong;std::getline(good,url);std::getline(bad,wrong);if(url.empty()||wrong.empty())return "blocked SMB config";
 diagnostic=log;redact={url,wrong};auto at=url.find('@');auto colon=url.find(':',6);if(at!=std::string::npos&&colon<at)redact.push_back(url.substr(colon+1,at-colon-1));
 struct Restore {~Restore(){av_log_set_callback(av_log_default_callback);diagnostic=nullptr;redact.clear();}} restore;av_log_set_callback(quiet);
 int sock=socket(AF_INET,SOCK_STREAM,0);int tcp=-1;
 if(sock>=0){fcntl(sock,F_SETFL,O_NONBLOCK);sockaddr_in a{};a.sin_family=AF_INET;a.sin_port=htons(1445);inet_pton(AF_INET,"192.168.3.199",&a.sin_addr);tcp=connect(sock,(sockaddr*)&a,sizeof(a));if(tcp<0&&errno==EINPROGRESS){pollfd f{sock,POLLOUT,0};if(poll(&f,1,3000)>0){int e=0;socklen_t n=sizeof(e);getsockopt(sock,SOL_SOCKET,SO_ERROR,&e,&n);tcp=e?-e:0;}}close(sock);}log("smb_fixture_tcp_rc="+std::to_string(tcp));
 p22_smb_options credentials,badCredentials;if(!p22_split_smb(url,credentials)||!p22_split_smb(wrong,badCredentials))return "failed malformed private fixture URL";
 redact.push_back(credentials.password);redact.push_back(badCredentials.password);

 AVIOContext *io=nullptr;double deadline=now()+15;AVIOInterruptCB cb={interrupt,&deadline};
 auto open=[&](const p22_smb_options &o,bool options,const std::string &path){
  AVDictionary *opts=nullptr;av_dict_set(&opts,"timeout","3000",0);
  if(options){av_dict_set(&opts,"username",o.user.c_str(),0);av_dict_set(&opts,"password",o.password.c_str(),0);}
  deadline=now()+10;int rc=avio_open2(&io,path.c_str(),AVIO_FLAG_READ,&cb,&opts);av_dict_free(&opts);return rc;
 };
 auto verify=[&](const std::string &label){
  int rc=0;std::vector<uint8_t> all;uint8_t b[65536];
  while(all.size()<=8388608){deadline=now()+10;rc=avio_read(io,b,sizeof(b));if(rc<=0)break;all.insert(all.end(),b,b+rc);}
  std::string digest=hash(all);log(label+" read bytes="+std::to_string(all.size())+" sha256="+digest+" end="+std::to_string(rc));
  if(all.size()!=8388608||digest!=seek_file_sha||rc!=AVERROR_EOF)return false;
  for(auto &r:seek_ranges){deadline=now()+10;int64_t pos=avio_seek(io,r.offset,SEEK_SET);std::vector<uint8_t> data(r.length);rc=avio_read(io,data.data(),data.size());std::string h=hash(data);log(label+" seek requested="+std::to_string(r.offset)+" returned="+std::to_string(pos)+" read="+std::to_string(rc)+" sha256="+h);if(pos!=r.offset||rc!=r.length||h!=r.sha)return false;}
  return true;
 };
 for(bool options:{false,true}){
  std::string label=options?"smb_options":"smb_url";
  int rc=open(badCredentials,options,options?badCredentials.url:wrong);log(label+" wrong_open_rc="+std::to_string(rc));
  if(rc>=0)avio_closep(&io);if(rc!=AVERROR(EACCES))return "failed wrong authentication result";
  rc=open(credentials,options,options?credentials.url:url);log(label+" correct_open_rc="+std::to_string(rc));
  if(rc<0)return "failed correct authentication";
  bool okay=verify(label);avio_closep(&io);if(!okay)return "failed SMB content or seek";
 }
 std::string missing=credentials.url.substr(0,credentials.url.find_last_of('/')+1)+"__missing_phase23.bin";
 int rc=open(credentials,true,missing);log("smb_missing_open_rc="+std::to_string(rc));if(rc>=0)avio_closep(&io);if(rc!=AVERROR(ENOENT))return "failed missing file result";
 std::string closed=credentials.url;auto port=closed.find(":1445/");if(port==std::string::npos)return "failed fixture port";closed.replace(port,6,":1446/");
 rc=open(credentials,true,closed);log("smb_closed_port_open_rc="+std::to_string(rc));if(rc>=0){avio_closep(&io);return "failed closed port accepted";}
 std::string drop=credentials.url.substr(0,credentials.url.find_last_of('/')+1)+"__phase23_disconnect.bin";
 rc=open(credentials,true,drop);log("smb_disconnect_open_rc="+std::to_string(rc));
 if(rc<0)return "failed disconnect fixture open";
 uint8_t block[65536];deadline=now()+10;rc=avio_read(io,block,sizeof(block));log("smb_forced_disconnect_read_rc="+std::to_string(rc));avio_closep(&io);
 if(rc>=0)return "failed server disconnect not observed";
 rc=open(credentials,true,credentials.url);log("smb_explicit_reopen_rc="+std::to_string(rc));if(rc<0)return "failed explicit reopen";
 bool okay=verify("smb_reopened");avio_closep(&io);
 return okay?"passed URL and AVOptions auth/read/seek, missing/closed-port, forced disconnect and explicit reopen; no transparent reconnect claim":"failed reopened data";
}
