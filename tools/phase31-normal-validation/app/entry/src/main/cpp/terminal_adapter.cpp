/* 此文件属于独立诊断应用，不属于libmpv。只终止自己的进程。 */
#include "terminal_adapter.h"
#include <mpv/ohcodec_terminal.h>
#include <atomic>
#include <pthread.h>
#include <unistd.h>
#include <fcntl.h>
#include <time.h>
#include <cstring>
#include <cstdio>
#include <cstdlib>
static std::atomic<int> configured{0},notifications{0};
static std::atomic<int64_t> cached_progress{0};
static std::atomic<int64_t> terminal_at{0};
static int event_fd=-1;
static int event_pipe[2]={-1,-1};
static std::atomic<int> terminal_error{0};
static std::atomic<bool> logger_fault{false};
struct EventMessage {int64_t timestamp;int code;char name[64];};
static bool hang_callback=false;
static int64_t ms(){struct timespec t{};clock_gettime(CLOCK_MONOTONIC,&t);return t.tv_sec*1000+t.tv_nsec/1000000;}
/* 小于PIPE_BUF的非阻塞投递；日志丢失不影响终局和退出。 */
static void event(const char *name,int code=0){EventMessage m{};m.timestamp=ms();m.code=code;snprintf(m.name,sizeof(m.name),"%s",name);if(event_pipe[1]>=0)write(event_pipe[1],&m,sizeof(m));}
static void disk_event(const char *name,int code,int64_t timestamp){char b[240];int n=snprintf(b,sizeof(b),"P29_APP t=%lld pid=%d event=%s code=%d\n",(long long)timestamp,getpid(),name,code);if(n>0&&event_fd>=0)write(event_fd,b,n);}
static void delay(){struct timespec d{0,20000000};nanosleep(&d,nullptr);}
static void receiver(const mpv_ohcodec_terminal_record*,void*){
 notifications.fetch_add(1);event("callback",notifications.load());
 while(hang_callback)delay();
}
static bool observe(){
 if(terminal_at.load(std::memory_order_acquire))return true;
 mpv_ohcodec_terminal_record r{};r.size=sizeof(r);r.abi_version=MPV_OHCODEC_TERMINAL_ABI_VERSION;
 if(mpv_ohcodec_terminal_snapshot(&r)!=1)return false;
 terminal_error.store(r.platform_error,std::memory_order_release);
 int64_t zero=0;terminal_at.compare_exchange_strong(zero,ms(),std::memory_order_acq_rel);
 return true;
}
static void *monitor(void*){
 for(;;){observe();const int64_t first=terminal_at.load(std::memory_order_acquire);
  if(first&&ms()>=first+3000)_Exit(86);delay();
 }
}
static void *logger(void*){
 bool seen=false;
 for(;;){
  if(logger_fault.load())for(;;)delay();
  EventMessage m{};while(read(event_pipe[0],&m,sizeof(m))==sizeof(m))disk_event(m.name,m.code,m.timestamp);
  const int64_t first=terminal_at.load(std::memory_order_acquire);
  if(first&&!seen){seen=true;disk_event("terminal-ready",terminal_error.load(),first);disk_event("cached-progress-ms",(int)cached_progress.load(),first);}
  delay();
 }
}
bool terminal_app_start(const char *root,const char *mode){
 int state=configured.load(std::memory_order_acquire);if(state==2)return terminal_app_admit();if(state!=0)return false;
 if(!strcmp(mode,"no-registration"))return false;
 int expected=0;if(!configured.compare_exchange_strong(expected,1))return false;
 char path[4096];if(snprintf(path,sizeof(path),"%s/terminal-events.log",root)>=(int)sizeof(path)){configured=3;return false;}
 event_fd=open(path,O_CREAT|O_WRONLY|O_APPEND|O_NONBLOCK,0600);if(event_fd<0){configured=3;return false;}
 if(pipe(event_pipe)){configured=3;return false;}
 if(fcntl(event_pipe[0],F_SETFL,O_NONBLOCK)||fcntl(event_pipe[1],F_SETFL,O_NONBLOCK)){configured=3;return false;}
 hang_callback=!strcmp(mode,"callback-hang");
 logger_fault.store(!strcmp(mode,"logger-hang"));
 pthread_t logging;if(pthread_create(&logging,nullptr,logger,nullptr)){configured=3;return false;}pthread_detach(logging);
 mpv_ohcodec_terminal_config c{};c.size=sizeof(c);c.abi_version=MPV_OHCODEC_TERMINAL_ABI_VERSION;c.handler=receiver;
 if(mpv_ohcodec_terminal_register(&c)){event("registration-failed");configured=3;return false;}
 pthread_t t;if(pthread_create(&t,nullptr,monitor,nullptr)){event("monitor-failed");configured=3;return false;}pthread_detach(t);
 if(mpv_ohcodec_terminal_enable()){event("enable-failed");configured=3;return false;}
 configured.store(2,std::memory_order_release);event("ready");return true;
}
bool terminal_app_admit(){return configured.load(std::memory_order_acquire)==2&&!observe();}
int terminal_app_state(){return observe()?1:0;}
void terminal_app_mark_ui(int code){event("ui",code);}
void terminal_app_cache_progress(int64_t value){if(!terminal_app_state())cached_progress.store(value);}
int64_t terminal_app_cached_progress(){return cached_progress.load();}
#ifdef TERMINAL_APP_HOST_TEST
extern "C" void *test_enter(void*);
void test_inject_terminal(){pthread_t t;pthread_create(&t,nullptr,test_enter,nullptr);pthread_detach(t);}
#endif
