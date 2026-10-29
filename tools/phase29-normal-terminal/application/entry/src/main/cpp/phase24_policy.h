#pragma once
#include <string>
#include <cmath>
#include <algorithm>
#include <cctype>
namespace p24 {
inline bool hardwareForMode(const std::string&mode){return !(mode.size()>=3&&mode.compare(mode.size()-3,3,"-sw")==0);}
struct Continuity {
 bool initialRestartSeen=false;std::string expectedGPU="ohos";
 void onRestart(){if(initialRestartSeen&&start>=0)interrupt("playback_restart");initialRestartSeen=true;}
 double start=-1,last=-1,firstPts=0,lastPts=0,stalled=0;unsigned samples=0;std::string reason;
 void interrupt(const std::string &r){if(reason.empty())reason=r;}
 void observe(double t,double pts,double speed,const std::string &hw,bool paused,bool valid,const std::string&gpu="ohos"){
  if(!initialRestartSeen)return;
  if(gpu!=expectedGPU)interrupt("gpu_context_mismatch");
  if(!valid||!std::isfinite(t)||!std::isfinite(pts)||!std::isfinite(speed)){interrupt("required_metric_unavailable");return;}
  if(std::abs(speed-1)>0.0001)interrupt("not_realtime_speed");
  if(hw!="ohcodec")interrupt("hardware_decode_not_observed");
  if(paused)interrupt("paused_or_cache_pause");
  if(start<0){start=last=t;firstPts=lastPts=pts;samples=1;return;}
  double dt=t-last,dp=pts-lastPts;
  if(dt<=0||dt>15)interrupt("clock_or_sampling_gap");
  if(dp<-.1||dp>dt+10)interrupt("media_discontinuity");
  stalled=dp<.01?stalled+dt:0;if(stalled>=15)interrupt("progress_stalled");
  if(std::abs((pts-firstPts)-(t-start))>10)interrupt("media_wall_clock_drift");
  last=t;lastPts=pts;samples++;
 }
 bool passed()const{return reason.empty()&&samples>=241&&start>=0&&last-start>=3600&&lastPts-firstPts>=3590;}
};
inline std::string safe_mpv_log(bool privateMedia,const std::string &level,const std::string &text){
 if(privateMedia)return {}; // No untrusted NAS text leaves libmpv client queue.
 std::string lower=text;std::transform(lower.begin(),lower.end(),lower.begin(),[](unsigned char c){return std::tolower(c);});
 if(lower.find("smb:")!=std::string::npos||lower.find("smb%3a")!=std::string::npos||lower.find("smb%253a")!=std::string::npos)return level+" [private transport message suppressed]";
 return level+" "+text;
}
}
