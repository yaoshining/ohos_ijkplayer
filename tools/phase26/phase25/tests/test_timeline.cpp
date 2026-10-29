#include "phase25_timeline.h"
#include <cassert>
#include <future>
#include <fstream>
#include <iostream>
#include <set>
#include <filesystem>
using namespace p25;
int main(int argc,char**argv){
 assert(argc==2);std::string root=argv[1];
 Session s(root,20,40);
 std::promise<void> entered,release;auto wait=release.get_future();
 auto worker=std::async(std::launch::async,[&]{return s.query(1,[&]{entered.set_value();wait.wait();return 7;});});
 entered.get_future().wait();std::this_thread::sleep_for(std::chrono::milliseconds(100));
 assert(s.beats()>=2);assert(s.overdues()>0);assert(worker.wait_for(std::chrono::milliseconds(0))==std::future_status::timeout);
 release.set_value();assert(worker.get()==7);
 auto before=s.events();std::thread a([&]{for(int i=0;i<20;i++)s.emit(Lane::UI,Event::Operator);});
 for(int i=0;i<20;i++)s.emit(Lane::Worker,Event::Operator);a.join();assert(s.events()>=before+40);
 State state;assert(state.apply(Event::AbilityForeground,1));assert(state.apply(Event::WindowInactive,1));assert(state.foreground());
 assert(state.apply(Event::StagePaused,1));assert(state.foreground());state.apply(Event::AbilityBackground,1);state.apply(Event::WindowActive,1);assert(!state.foreground());assert(state.interrupted());
 assert(state.apply(Event::SurfaceCreate,2));assert(!state.apply(Event::SurfaceDestroy,1));assert(state.surface()==2);state.apply(Event::SurfaceDestroy,2);assert(!state.apply(Event::SurfaceCreate,2));assert(state.apply(Event::SurfaceCreate,3));
 state.apply(Event::AbilityDestroy,0);assert(!state.apply(Event::AbilityForeground,0));assert(!state.apply(Event::SurfaceCreate,4));
 int n=0;auto shortWriter=[&](int,const void*,size_t len)->ssize_t {if(n++==0){errno=EINTR;return -1;}return len>2?2:len;};assert(writeAll(1,"abcdef",6,shortWriter));
 auto bad=[](int,const void*,size_t)->ssize_t {errno=ENOSPC;return -1;};assert(!writeAll(1,"a",1,bad));
 assert(s.query(8,[]{return -8;})==-8);
 s.close();assert(s.errors()==0);
 bool failedRc=false;for(const auto &entry: std::filesystem::directory_iterator(root)){std::ifstream f(entry.path());std::string row;while(std::getline(f,row))if(row.find("\"event\":\"query_end\"")!=std::string::npos&&row.find("\"rc\":-8")!=std::string::npos)failedRc=true;}assert(failedRc);assert(!s.emit(Lane::UI,Event::Operator));
 Session failed(root+"/absent/child",20,40);assert(failed.errors()>0);failed.close();
 std::filesystem::create_directory(root+"/slow-sink");
 std::promise<void> sinkEntered,sinkRelease;auto sinkWait=sinkRelease.get_future();
 auto sink=[&](int fd,const void*buf,size_t n)->ssize_t {std::string line((const char*)buf,n);if(line.find("\"event\":\"query_begin\"")!=std::string::npos){sinkEntered.set_value();sinkWait.wait();}return ::write(fd,buf,n);};
 Session io(root+"/slow-sink",20,40,sink);
 auto fast=std::async(std::launch::async,[&]{return io.query(9,[]{return 0;});});
 sinkEntered.get_future().wait();std::this_thread::sleep_for(std::chrono::milliseconds(120));assert(io.beats()>=3);sinkRelease.set_value();assert(fast.get()==0);io.close();assert(io.overdues()==0);
 bool found=false;
 for(const auto &entry: std::filesystem::directory_iterator(root+"/slow-sink")){std::ifstream f(entry.path());std::string line;while(std::getline(f,line))if(line.find("\"event\":\"query_end\"")!=std::string::npos){auto p=line.find("\"durationNs\":")+13;auto duration=std::stoll(line.substr(p));assert(duration<40000000);assert(line.find("\"callStartNs\":")!=std::string::npos);found=true;}}
 assert(found);
 std::cout<<"PASS blocked-query heartbeat, overdue, recovery, concurrent seq, lifecycle domains, late generation, EINTR/shortwrite/ENOSPC, terminal/open failure\n";
}
