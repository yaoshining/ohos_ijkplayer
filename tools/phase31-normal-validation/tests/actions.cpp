#include "phase31_actions.h"
#include "include/mpv/client.h"
extern "C" int mpv_command(mpv_handle*,const char **args){return args&&args[0]?0:-4;}
#include <cstdio>
#include <string>
using namespace p31;
static int errors=0;
#define CHECK(x) do { if(!(x)){std::printf("FAIL line=%d %s\n",__LINE__,#x);errors++;}}while(0)
static Observation o(double t,double pts,bool pause=false){return {t,pts,true,pause,true};}
static void seekReady(Controller &c,double now,double target){c.seekEvent();c.restartEvent();CHECK(c.observe(o(now,target))==Action::None);}
int main(){
 { Controller c;CHECK(c.observe(o(1,1))==Action::None);CHECK(c.observe(o(3,3))==Action::Seek30);c.commandResult(0);seekReady(c,4,30);CHECK(c.observe(o(7,33))==Action::Pause);c.commandResult(0);CHECK(c.observe(o(7.1,33,true))==Action::None);for(double t=7.35;t<10.1;t+=.25)CHECK(c.observe(o(t,33,true))==Action::None);CHECK(c.observe(o(10.2,33,true))==Action::Resume);c.commandResult(0);CHECK(c.observe(o(13.3,36.2))==Action::Seek5);c.commandResult(0);seekReady(c,14,5);CHECK(c.observe(o(17.2,8.2))==Action::Done);CHECK(c.passed()); }
 { Controller c;c.observe(o(3,3));c.commandResult(-12);CHECK(c.failed());CHECK(c.reason=="command_failed"); }
 { Controller c;c.observe(o(3,3));c.commandResult(0);CHECK(c.observe(o(19,30))==Action::Fail);CHECK(c.reason=="seek_forward_timeout"); }
 { Controller c;c.observe(o(3,3));c.commandResult(0);c.seekEvent();c.restartEvent();CHECK(c.observe(o(4,35))==Action::None);CHECK(c.observe(o(19,48))==Action::Fail); }
 { Controller c;c.observe(o(3,3));c.commandResult(0);seekReady(c,4,30);c.observe(o(7,33));c.commandResult(0);c.observe(o(7.1,33,true));CHECK(c.observe(o(7.2,34,true))==Action::Fail);CHECK(c.reason=="pause_drift"); }
 { Controller c;c.observe(o(3,3));c.commandResult(0);seekReady(c,4,30);c.observe(o(7,33));c.commandResult(0);CHECK(c.observe(o(23,48))==Action::Fail);CHECK(c.reason=="pause_timeout"); }
 { Controller c;auto q=o(3,3);q.ptsValid=false;CHECK(c.observe(q)==Action::None);CHECK(c.observe(o(21,0))==Action::Fail); }
 { int calls=0;auto command=[&](const char *const*a){calls++;CHECK(std::string(a[0])=="seek");CHECK(std::string(a[1])=="30");CHECK(std::string(a[2])=="absolute+exact");return 0;};auto pause=[&](int p){calls++;CHECK(p==1);return 0;};CHECK(apply(Action::Seek30,command,pause)==0);CHECK(apply(Action::Pause,command,pause)==0);CHECK(calls==2); }
 { Controller c;c.observe(o(3,3));c.commandResult(0);seekReady(c,4,30);c.observe(o(7,33));c.commandResult(0);c.observe(o(7.1,33,true));CHECK(c.observe(o(7.2,33.1,false))==Action::Fail);CHECK(c.reason=="pause_interrupted"); }
 { Controller c;c.observe(o(3,3));c.commandResult(0);seekReady(c,4,30);c.observe(o(7,33));c.commandResult(0);c.observe(o(7.1,33,true));auto q=o(7.2,33,true);q.ptsValid=false;CHECK(c.observe(q)==Action::Fail);CHECK(c.reason=="pause_observation_invalid"); }
 { Controller c;c.observe(o(3,3));c.commandResult(0);seekReady(c,4,30);c.observe(o(7,33));c.commandResult(0);c.observe(o(7.1,33,true));CHECK(c.observe(o(10.2,33,true))==Action::Fail);CHECK(c.reason=="pause_sampling_gap"); }
 { Controller c;c.observe(o(1,1));CHECK(c.observe(o(.9,1))==Action::Fail);CHECK(c.reason=="clock_regression"); }
 { auto command=[](const char**args){return mpv_command(nullptr,args);};auto pause=[](int){return 0;};CHECK(apply(Action::Seek5,command,pause)==0); }
 std::printf("%s actual-operation-controller cases=13\n",errors?"FAIL":"PASS");return errors?1:0;
}
