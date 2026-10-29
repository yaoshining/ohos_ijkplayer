#pragma once
#include <atomic>
#include <chrono>
#include <condition_variable>
#include <cstdint>
#include <cstdio>
#include <functional>
#include <mutex>
#include <string>
#include <thread>
#include <fcntl.h>
#include <unistd.h>
#include <errno.h>
#include <time.h>
namespace p25 {
enum class Lane { UI, Worker, Heartbeat };
enum class Event { SessionBegin, SessionEnd, SampleBegin, SampleEnd, QueryBegin, QueryEnd, Heartbeat, Overdue,
 AbilityCreate, AbilityForeground, AbilityBackground, AbilityDestroy, StageCreate, StageShown, StageResumed, StagePaused, StageHidden, StageDestroy,
 WindowActive, WindowInactive, SurfaceCreate, SurfaceDestroy, Late, SubscriptionFailed, Operator, LoggingError, FaultDelay, RunBegin, RunEnd, KeepAwakeRequest, KeepAwakeSuccess, KeepAwakeReadback, KeepAwakeFailure };
inline const char* eventName(Event e){static const char* names[]={"session_begin","session_end","sample_begin","sample_end","query_begin","query_end","heartbeat","overdue","ability_create","ability_foreground","ability_background","ability_destroy","stage_create","stage_shown","stage_resumed","stage_paused","stage_hidden","stage_destroy","window_active","window_inactive","surface_create","surface_destroy","late_event","subscription_failed","operator_action","logging_error","fault_delay","run_begin","run_end","keep_awake_request","keep_awake_success","keep_awake_readback","keep_awake_failure"};auto n=(unsigned)e;return n<sizeof(names)/sizeof(*names)?names[n]:nullptr;}
inline int64_t clockNs(clockid_t id){timespec t{};if(clock_gettime(id,&t))return 0;return int64_t(t.tv_sec)*1000000000+t.tv_nsec;}
template<class Writer> bool writeAll(int fd,const char*p,size_t n,Writer writeFn){while(n){ssize_t r=writeFn(fd,p,n);if(r<0&&errno==EINTR)continue;if(r<=0||size_t(r)>n)return false;p+=r;n-=r;}return true;}
// 本模型由UI线程单独拥有，worker只读Session中的atomic后台标志。
class State {
 bool fg=false,inter=false,terminal=false;unsigned current=0,dead=0;
public:
 bool apply(Event e,unsigned generation){
  if(terminal)return false;
  if(e==Event::AbilityDestroy){terminal=true;fg=false;}
  if(e==Event::SurfaceCreate){if(generation<=dead||generation<current)return false;current=generation;}
  if(e==Event::SurfaceDestroy){if(generation!=current||generation<=dead)return false;dead=generation;current=0;}
  if(e==Event::AbilityForeground)fg=true;
  if(e==Event::AbilityBackground){fg=false;inter=true;}
  return true;
 }
 bool foreground()const{return fg;}bool interrupted()const{return inter;}unsigned surface()const{return current;}
};
class Session {
 int fd[3]{-1,-1,-1};std::mutex lanes[3],sleepLock;std::condition_variable wake;
 std::atomic<uint64_t> seq{0},beatCount{0},overdueCount{0},errorCount{0},active{0};
 std::atomic<int64_t> activeStart{0};std::atomic<bool> stopping{false},closed{false};std::thread heartbeat;
 std::string id;int interval,limit;std::function<ssize_t(int,const void*,size_t)> writer;
public:
 std::atomic<bool> backgroundSeen{false};
 Session(const std::string&root,int intervalMs=500,int overdueMs=2000,std::function<ssize_t(int,const void*,size_t)> sink=::write):interval(intervalMs),limit(overdueMs),writer(sink){
  char buf[80];snprintf(buf,sizeof(buf),"%llx-%x-%llx",(unsigned long long)clockNs(CLOCK_REALTIME),getpid(),(unsigned long long)clockNs(CLOCK_MONOTONIC));id=buf;
  const char*names[]={"ui","worker","heartbeat"};for(int i=0;i<3;i++){auto path=root+"/timeline-"+id+"-"+names[i]+".jsonl";fd[i]=open(path.c_str(),O_WRONLY|O_CREAT|O_EXCL|O_APPEND|O_CLOEXEC,0600);if(fd[i]<0)++errorCount;}
  emit(Lane::UI,Event::SessionBegin,0,0,0,getpid());
  heartbeat=std::thread([this]{std::unique_lock<std::mutex> l(sleepLock);while(!wake.wait_for(l,std::chrono::milliseconds(interval),[this]{return stopping.load();})){
   l.unlock();++beatCount;auto q=active.load(std::memory_order_acquire);emit(Lane::Heartbeat,Event::Heartbeat,q);auto t=activeStart.load();auto age=clockNs(CLOCK_MONOTONIC)-t;
   if(q&&q==active.load(std::memory_order_acquire)&&age>int64_t(limit)*1000000){++overdueCount;emit(Lane::Heartbeat,Event::Overdue,q,0,age);}l.lock();}});
 }
 ~Session(){close();}Session(const Session&)=delete;Session&operator=(const Session&)=delete;
 uint64_t emit(Lane lane,Event event,uint64_t key=0,unsigned generation=0,int64_t duration=0,int rc=0,int64_t callStart=0){
  auto name=eventName(event);auto i=(unsigned)lane;if(!name||i>2){++errorCount;return 0;}
  std::lock_guard<std::mutex> lock(lanes[i]);if(closed)return 0;
  auto n=++seq;char line[768];auto mono=clockNs(CLOCK_MONOTONIC),wall=clockNs(CLOCK_REALTIME);
  int size=snprintf(line,sizeof(line),"{\"schema\":1,\"session\":\"%s\",\"seq\":%llu,\"lane\":%u,\"event\":\"%s\",\"key\":%llu,\"generation\":%u,\"monoNs\":%lld,\"wallNs\":%lld,\"durationNs\":%lld,\"rc\":%d,\"callStartNs\":%lld}\n",id.c_str(),(unsigned long long)n,i,name,(unsigned long long)key,generation,(long long)mono,(long long)wall,(long long)duration,rc,(long long)callStart);
  if(size<=0||size>=int(sizeof(line))||fd[i]<0||!writeAll(fd[i],line,size,writer))++errorCount;
  if(event==Event::AbilityBackground||event==Event::AbilityDestroy||event==Event::SessionEnd){if(fd[i]<0||fsync(fd[i]))++errorCount;}
  return n;
 }
 template<class F> auto query(unsigned property,F fn)->decltype(fn()){
  auto key=emit(Lane::Worker,Event::QueryBegin,0,property);
  // 此前的同步日志写入不计入调用耗时。BEGIN是记录边界；真实调用起点随END持久化。
  auto start=clockNs(CLOCK_MONOTONIC);
  activeStart.store(start);active.store(key,std::memory_order_release);
  auto result=fn();auto end=clockNs(CLOCK_MONOTONIC);active.store(0,std::memory_order_release);
  emit(Lane::Worker,Event::QueryEnd,key,property,end-start,int(result),start);return result;
 }
 uint64_t beats()const{return beatCount;}uint64_t overdues()const{return overdueCount;}uint64_t events()const{return seq;}uint64_t errors()const{return errorCount;}
 void noteError(){++errorCount;}
 void close(){if(closed)return;stopping=true;wake.notify_all();if(heartbeat.joinable())heartbeat.join();
  // 调用者必须已经回收所有worker；UI完成后才关闭，不能在blocked getter期间调用。
  for(int i=0;i<3;i++)if(fd[i]>=0&&fsync(fd[i]))++errorCount;
  emit(Lane::UI,Event::SessionEnd,0,0,0,(int)errorCount.load());
  std::scoped_lock l(lanes[0],lanes[1],lanes[2]);closed=true;for(auto&f:fd){if(f>=0)::close(f);f=-1;}}
};
}
