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
 AVIOContext *io=nullptr;double deadline=now()+15;AVIOInterruptCB cb={interrupt,&deadline};int rc=avio_open2(&io,wrong.c_str(),AVIO_FLAG_READ,&cb,nullptr);log("smb_wrong_open_rc="+std::to_string(rc));if(rc>=0){avio_closep(&io);return "failed wrong password accepted";}
 deadline=now()+15;rc=avio_open2(&io,url.c_str(),AVIO_FLAG_READ,&cb,nullptr);log("smb_correct_open_rc="+std::to_string(rc));if(rc<0){
 auto openOptions=[&](p22_smb_options &o){AVDictionary *opts=nullptr;av_dict_set(&opts,"username",o.user.c_str(),0);av_dict_set(&opts,"password",o.password.c_str(),0);av_dict_set(&opts,"timeout","5000",0);deadline=now()+15;int r=avio_open2(&io,o.url.c_str(),AVIO_FLAG_READ,&cb,&opts);av_dict_free(&opts);return r;};
 rc=openOptions(badCredentials);log("smb_options_wrong_open_rc="+std::to_string(rc));if(rc>=0){avio_closep(&io);return "failed options wrong password accepted";}
 rc=openOptions(credentials);log("smb_options_correct_open_rc="+std::to_string(rc));if(rc<0)return "blocked SMB URL and options open "+std::to_string(rc);
 }
 std::vector<uint8_t> all;uint8_t b[65536];while(all.size()<=8388608){deadline=now()+10;rc=avio_read(io,b,sizeof(b));if(rc<=0)break;all.insert(all.end(),b,b+rc);}std::string digest=hash(all);log("smb_read bytes="+std::to_string(all.size())+" sha256="+digest+" end="+std::to_string(rc));
 if(all.size()!=8388608||digest!=seek_file_sha||rc!=AVERROR_EOF){avio_closep(&io);return "failed SMB content";}
 for(auto &r:seek_ranges){deadline=now()+10;int64_t pos=avio_seek(io,r.offset,SEEK_SET);std::vector<uint8_t> data(r.length);rc=avio_read(io,data.data(),data.size());std::string h=hash(data);log("smb_seek requested="+std::to_string(r.offset)+" returned="+std::to_string(pos)+" read="+std::to_string(rc)+" sha256="+h);if(pos!=r.offset||rc!=r.length||h!=r.sha){avio_closep(&io);return "failed SMB seek";}}
 avio_closep(&io);return "passed SMB read and six seek ranges; reconnect not tested";
}
