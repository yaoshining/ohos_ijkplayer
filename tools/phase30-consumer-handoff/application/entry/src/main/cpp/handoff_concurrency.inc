#include <dlfcn.h>
#include <pthread.h>
#include <mutex>
extern "C" unsigned avcodec_version(void);
struct P30Snapshot { uint64_t state,decoder,callback_tid,close_tid,epoch; };
static void p30_concurrent(mpv_handle *p,const std::string &root){
 void *codecLib=dlopen("libavcodec.so.62",RTLD_NOW|RTLD_LOCAL|RTLD_NOLOAD);
 void *mpvLib=dlopen("libmpv.so",RTLD_NOW|RTLD_LOCAL|RTLD_NOLOAD);
 auto arm=(int(*)(uint64_t))dlsym(codecLib,"av_ohcodec_handoff_test_arm");
 auto snapshot=(int(*)(P30Snapshot*))dlsym(codecLib,"av_ohcodec_handoff_test_snapshot");
 auto release=(int(*)())dlsym(codecLib,"av_ohcodec_handoff_test_release");
 auto waiting=(int(*)(uint64_t*,int))dlsym(mpvLib,"mpv_ohcodec_handoff_test_waiting");
 std::ofstream trace(root+"/handoff-concurrency.log");std::mutex mu;unsigned sequence=0;
 auto event=[&](const std::string &op){std::lock_guard<std::mutex> guard(mu);trace<<"P30_APP seq="<<++sequence<<" t="<<(int64_t)(mono()*1000000)<<" pid="<<getpid()<<" tid="<<pthread_gettid_np(pthread_self())<<" "<<op<<std::endl;};
 auto done=std::make_shared<std::atomic_bool>(false);
 std::thread([done]{auto until=std::chrono::steady_clock::now()+std::chrono::seconds(15);while(!done->load()){if(std::chrono::steady_clock::now()>=until)_Exit(87);std::this_thread::sleep_for(std::chrono::milliseconds(10));}}).detach();
 auto fail=[&](const char *why){if(release)release();event(std::string("op=failed reason=")+why);_Exit(87);};
 event("op=api-visible codec="+std::to_string(codecLib!=nullptr)+" mpv="+std::to_string(mpvLib!=nullptr)+" arm="+std::to_string(arm!=nullptr)+" snapshot="+std::to_string(snapshot!=nullptr)+" release="+std::to_string(release!=nullptr)+" waiting="+std::to_string(waiting!=nullptr));
 if(!codecLib||!mpvLib||!arm||!snapshot||!release||!waiting)fail("missing-test-api");
 Dl_info codecAnchor{},mpvAnchor{},api{};
 if(!dladdr((void*)avcodec_version,&codecAnchor)||!dladdr((void*)mpv_create,&mpvAnchor))fail("anchor-dladdr");
 for(void *fn:{(void*)arm,(void*)snapshot,(void*)release}){if(!dladdr(fn,&api)||api.dli_fbase!=codecAnchor.dli_fbase)fail("wrong-codec-mapping");event(std::string("op=api-mapping library=codec path=")+api.dli_fname);}
 if(!dladdr((void*)waiting,&api)||api.dli_fbase!=mpvAnchor.dli_fbase)fail("wrong-mpv-mapping");event(std::string("op=api-mapping library=mpv path=")+api.dli_fname);
 if(arm(1))fail("arm-rejected");event("op=armed decoder=1");
 std::string next=root+"/pq2-bounded.mp4",last=root+"/hlg-bounded.mp4";
 std::thread trigger([&]{event("op=trigger-enter");const char *cmd[]={"loadfile",next.c_str(),nullptr};int rc=mpv_command(p,cmd);event("op=trigger-return rc="+std::to_string(rc));});
 P30Snapshot s{};auto limit=mono()+5;
 while(mono()<limit){snapshot(&s);if(s.state==4)break;if(s.state==7)fail("callback-window-timeout");std::this_thread::sleep_for(std::chrono::milliseconds(1));}
 if(s.state!=4)fail("no-actual-close-wait");event("op=close-wait-confirmed decoder="+std::to_string(s.decoder)+" epoch="+std::to_string(s.epoch)+" callback_tid="+std::to_string(s.callback_tid)+" close_tid="+std::to_string(s.close_tid));
 std::atomic<uint64_t> ta{0},tb{0};std::atomic_bool ca{false},cb{false};
 std::thread a([&]{ta=pthread_gettid_np(pthread_self());event("op=request-enter request=load");const char *cmd[]={"loadfile",last.c_str(),nullptr};int rc=mpv_command(p,cmd);ca=true;event("op=request-return request=load rc="+std::to_string(rc));});
 std::thread b([&]{tb=pthread_gettid_np(pthread_self());event("op=request-enter request=seek");const char *cmd[]={"seek","0","absolute",nullptr};int rc=mpv_command(p,cmd);cb=true;event("op=request-return request=seek rc="+std::to_string(rc));});
 bool both=false;limit=mono()+3;
 while(mono()<limit){uint64_t ids[32]={0};int n=waiting(ids,32);bool aa=false,bb=false;for(int i=0;i<n;i++){aa|=ta.load()!=0&&ids[i]==ta;bb|=tb.load()!=0&&ids[i]==tb;}if(aa&&bb&&!ca&&!cb){both=true;break;}std::this_thread::sleep_for(std::chrono::milliseconds(1));}
 if(!both)fail("requests-not-in-real-dispatch-wait");
 event("op=two-dispatch-waits request_a_tid="+std::to_string(ta)+" request_b_tid="+std::to_string(tb));snapshot(&s);if(s.state!=4)fail("close-wait-lost-before-release");event("op=callback-release");release();
 trigger.join();a.join();b.join();snapshot(&s);if(s.state!=6)fail("callback-not-released");event("op=joined callback_state=6");done->store(true);
}
