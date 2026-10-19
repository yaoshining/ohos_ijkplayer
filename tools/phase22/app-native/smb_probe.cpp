#include "smb_probe.h"
#include "seek_expected.h"
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
static void quiet(void*,int,const char*,va_list){}
static std::string hash(const std::vector<uint8_t> &v){AVSHA *s=av_sha_alloc();av_sha_init(s,256);av_sha_update(s,v.data(),v.size());uint8_t d[32];av_sha_final(s,d);av_free(s);char b[65];for(int i=0;i<32;i++)sprintf(b+2*i,"%02x",d[i]);return b;}
std::string p22_smb_read(const std::string &root,std::function<void(const std::string&)> log){
 std::ifstream good(root+"/smb-test.txt"),bad(root+"/smb-wrong.txt");std::string url,wrong;std::getline(good,url);std::getline(bad,wrong);if(url.empty()||wrong.empty())return "blocked SMB config";
 struct Restore {~Restore(){av_log_set_callback(av_log_default_callback);}} restore;av_log_set_callback(quiet);
 AVIOContext *io=nullptr;double deadline=now()+15;AVIOInterruptCB cb={interrupt,&deadline};int rc=avio_open2(&io,wrong.c_str(),AVIO_FLAG_READ,&cb,nullptr);log("smb_wrong_open_rc="+std::to_string(rc));if(rc>=0){avio_closep(&io);return "failed wrong password accepted";}
 deadline=now()+15;rc=avio_open2(&io,url.c_str(),AVIO_FLAG_READ,&cb,nullptr);log("smb_correct_open_rc="+std::to_string(rc));if(rc<0)return "failed SMB open "+std::to_string(rc);
 std::vector<uint8_t> all;uint8_t b[65536];while(all.size()<=8388608){deadline=now()+10;rc=avio_read(io,b,sizeof(b));if(rc<=0)break;all.insert(all.end(),b,b+rc);}std::string digest=hash(all);log("smb_read bytes="+std::to_string(all.size())+" sha256="+digest+" end="+std::to_string(rc));
 if(all.size()!=8388608||digest!=seek_file_sha||rc!=AVERROR_EOF){avio_closep(&io);return "failed SMB content";}
 for(auto &r:seek_ranges){deadline=now()+10;int64_t pos=avio_seek(io,r.offset,SEEK_SET);std::vector<uint8_t> data(r.length);rc=avio_read(io,data.data(),data.size());std::string h=hash(data);log("smb_seek requested="+std::to_string(r.offset)+" returned="+std::to_string(pos)+" read="+std::to_string(rc)+" sha256="+h);if(pos!=r.offset||rc!=r.length||h!=r.sha){avio_closep(&io);return "failed SMB seek";}}
 avio_closep(&io);return "passed SMB read and six seek ranges; reconnect not tested";
}
