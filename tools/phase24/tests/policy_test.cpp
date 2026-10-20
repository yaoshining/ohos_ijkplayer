#include "phase24_policy.h"
#include <cassert>
using namespace p24;
static void started(Continuity&c){c.onRestart();}
int main(){
 assert(hardwareForMode("gl-switch"));assert(hardwareForMode("vk-switch"));assert(hardwareForMode("gl-pq-rgb10"));
 assert(!hardwareForMode("gl-pq-sw"));assert(!hardwareForMode("vk-sdr-sw"));

 Continuity delayed;
 delayed.observe(0,0,1,"ohcodec",false,true,"ohos");assert(delayed.start<0);
 delayed.onRestart();delayed.observe(5,5,1,"ohcodec",false,true,"ohos");assert(delayed.reason.empty());
 delayed.onRestart();assert(delayed.reason=="playback_restart");
 Continuity gpu;started(gpu);gpu.expectedGPU="ohosvk";
 gpu.observe(0,0,1,"ohcodec",false,true,"ohos");assert(gpu.reason=="gpu_context_mismatch");

 Continuity ok;started(ok); for(int i=0;i<=3600;i+=5) ok.observe(i,i,1,"ohcodec",false,true); assert(ok.passed());
 Continuity shortRun;started(shortRun); for(int i=0;i<=60;i+=5)shortRun.observe(i,i,1,"ohcodec",false,true); assert(!shortRun.passed());
 Continuity sw;started(sw); for(int i=0;i<=3600;i+=5)sw.observe(i,i,1,i==1800?"no":"ohcodec",false,true);assert(!sw.passed());
 Continuity eof=ok;eof.interrupt("early_eof");assert(!eof.passed());
 Continuity gap;started(gap);gap.observe(0,0,1,"ohcodec",false,true);gap.observe(3600,3600,1,"ohcodec",false,true);assert(!gap.passed());
 Continuity paused;started(paused);paused.observe(0,0,1,"ohcodec",false,true);paused.observe(5,0,1,"ohcodec",true,true);assert(!paused.reason.empty());
 Continuity missing;started(missing);missing.observe(0,0,1,"ohcodec",false,false);assert(!missing.reason.empty());
 Continuity speed;started(speed);speed.observe(0,0,2,"ohcodec",false,true);assert(!speed.reason.empty());
 Continuity back;started(back);back.observe(5,5,1,"ohcodec",false,true);back.observe(4,4,1,"ohcodec",false,true);assert(!back.reason.empty());
 Continuity jump;started(jump);jump.observe(0,0,1,"ohcodec",false,true);jump.observe(5,500,1,"ohcodec",false,true);assert(!jump.reason.empty());
 Continuity nan;started(nan);nan.observe(0,NAN,1,"ohcodec",false,true);assert(!nan.reason.empty());
 assert(safe_mpv_log(true,"error","failed smb://user:p%40ss@host/私人.mp4").empty());
 assert(safe_mpv_log(true,"debug","private filename without URL").empty());
 assert(safe_mpv_log(false,"warn","SetColorSpace failed rc=12")=="warn SetColorSpace failed rc=12");
 assert(safe_mpv_log(false,"debug","smb://user:pass@host/file").find("pass")==std::string::npos);
 assert(safe_mpv_log(false,"error","smb%3A%2F%2Fuser%3Asecret%40host").find("secret")==std::string::npos);
}
