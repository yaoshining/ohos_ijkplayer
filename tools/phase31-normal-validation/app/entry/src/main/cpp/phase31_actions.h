#pragma once
#include <cmath>
#include <string>
namespace p31 {
enum class Action {None,Seek30,Pause,Resume,Seek5,Done,Fail};
struct Observation {double now,pts;bool ptsValid,paused,pauseValid;};
struct Controller {
 int stage=0;double since=0,anchor=0,pauseSince=-1,lastTime=-1;bool seek=false,restart=false;std::string reason;
 bool passed()const{return stage==7&&reason.empty();}bool failed()const{return !reason.empty();}
 void commandResult(int rc){if(rc<0)reason="command_failed";}
 void seekEvent(){seek=true;}void restartEvent(){restart=true;}
 Action fail(const char*r){reason=r;return Action::Fail;}
 Action move(int s,Action a,double t){stage=s;since=t;return a;}
 Action observe(Observation o){
  if(failed())return Action::Fail;if(passed())return Action::Done;
  if(!std::isfinite(o.now)||o.now<0)return fail("invalid_clock");
  double gap=lastTime<0?0:o.now-lastTime;if(gap<0)return fail("clock_regression");lastTime=o.now;
  if(stage==3&&pauseSince>=0){if(!o.ptsValid||!o.pauseValid||!std::isfinite(o.pts))return fail("pause_observation_invalid");if(!o.paused)return fail("pause_interrupted");if(gap>.5)return fail("pause_sampling_gap");}
  if(o.now-since>(stage==0?20:15)){
   const char*names[]={"initial_timeout","seek_forward_timeout","forward_progress_timeout","pause_timeout","resume_timeout","seek_backward_timeout","backward_progress_timeout"};return fail(names[stage]);}
  if(!o.ptsValid||!o.pauseValid||!std::isfinite(o.pts))return Action::None;
  if(stage==0&&o.pts>=3&&!o.paused){seek=restart=false;return move(1,Action::Seek30,o.now);}
  if((stage==1||stage==5)&&seek&&restart&&std::abs(o.pts-(stage==1?30:5))<=2&&!o.paused){anchor=o.pts;return move(stage==1?2:6,Action::None,o.now);}
  if(stage==2&&o.pts-anchor>=3&&!o.paused){pauseSince=-1;return move(3,Action::Pause,o.now);}
  if(stage==3&&o.paused){if(pauseSince<0){pauseSince=o.now;anchor=o.pts;}if(std::abs(o.pts-anchor)>.25)return fail("pause_drift");if(o.now-pauseSince>=3)return move(4,Action::Resume,o.now);}
  if(stage==4&&!o.paused&&o.pts-anchor>=3){seek=restart=false;return move(5,Action::Seek5,o.now);}
  if(stage==6&&!o.paused&&o.pts-anchor>=3)return move(7,Action::Done,o.now);
  return Action::None;
 }
};
template<class C,class P>int apply(Action a,C command,P pause){
 if(a==Action::Seek30||a==Action::Seek5){const char*args[]={"seek",a==Action::Seek30?"30":"5","absolute+exact",nullptr};return command(args);}
 if(a==Action::Pause||a==Action::Resume)return pause(a==Action::Pause?1:0);
 return 0;
}
}
