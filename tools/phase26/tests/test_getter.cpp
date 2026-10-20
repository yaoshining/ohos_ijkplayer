#include "phase25_mpv.h"
#include <cassert>
#include <fstream>
#include <filesystem>
#include <string>
#include <vector>
extern int p22_sample_video(mpv_handle*,double*);
static std::vector<std::string> names;
static int result=0;
extern "C" int mpv_get_property(mpv_handle*,const char*n,mpv_format,void*) {names.emplace_back(n);return result;}
int main(int argc,char**argv){
 assert(argc==2);double pts=0;assert(p25::get(nullptr,"time-pos",MPV_FORMAT_DOUBLE,&pts)==MPV_ERROR_UNINITIALIZED);assert(names.empty());
 p25::Session s(argv[1],20,40);p25::workerSession=&s;
 result=-8;for(auto format:{MPV_FORMAT_FLAG,MPV_FORMAT_STRING,MPV_FORMAT_NODE})assert(p25::get(nullptr,"video-dec-params",format,&pts)==-8);
 names.clear();assert(p22_sample_video(nullptr,&pts)==-8);assert(names.size()==1&&names[0]=="video-frame-info/interlaced");
 result=0;names.clear();assert(p22_sample_video(nullptr,&pts)==0);assert(names.size()==2&&names[1]=="time-pos");
 auto count=names.size();assert(p25::get(nullptr,"unapproved-property",MPV_FORMAT_DOUBLE,&pts)==MPV_ERROR_INVALID_PARAMETER);assert(names.size()==count);assert(s.errors()==1);
 p25::workerSession=nullptr;s.close();unsigned negatives=0;for(auto&e:std::filesystem::directory_iterator(argv[1])){std::ifstream f(e.path());std::string line;while(std::getline(f,line))if(line.find("\"event\":\"query_end\"")!=std::string::npos&&line.find("\"rc\":-8")!=std::string::npos)negatives++;}assert(negatives==4);
}
