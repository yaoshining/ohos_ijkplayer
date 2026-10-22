#pragma once
#include <string>
#include <functional>
#include <fstream>
#include <sys/stat.h>
#include <unistd.h>
#include <cerrno>
inline bool p22_resource_case(const std::string &root,const std::string &mode,std::function<int()> validate,std::function<void(std::string)> log){
 std::string path=root+(mode=="cache-permission"?"/cache":mode=="missing-cache-directory"?"/cache/demux":"/resources/fonts/font1.ttf"),backup=root+"/.phase22-resource-backup";
 bool perm=mode=="font-permission"||mode=="cache-permission";
 if(!perm&&mode!="missing-font"&&mode!="missing-cache-directory"&&mode!="bad-font"&&mode!="font-symlink")return false;
 struct stat s;if(lstat(path.c_str(),&s)||access(backup.c_str(),F_OK)==0)return false;
 int expected=perm?EACCES:(mode=="missing-font"||mode=="missing-cache-directory")?ENOENT:EINVAL;
 if(perm){if(chmod(path.c_str(),mode=="cache-permission"?0500:0000))return false;}
 else {if(rename(path.c_str(),backup.c_str()))return false;if(mode=="bad-font"){std::ofstream f(path);f<<"invalid";}if(mode=="font-symlink"&&symlink(backup.c_str(),path.c_str())){int err=errno;rename(backup.c_str(),path.c_str());log("resource_negative="+mode+" setup_blocked_errno="+std::to_string(err));return false;}}
 int observed=validate();
 int restore=0;if(perm)restore=chmod(path.c_str(),s.st_mode&0777);else{if(mode!="missing-font"&&mode!="missing-cache-directory")unlink(path.c_str());restore=rename(backup.c_str(),path.c_str());}
 log("resource_negative="+mode+" expected="+std::to_string(expected)+" observed="+std::to_string(observed)+" restore="+std::to_string(restore));
 return observed==expected&&restore==0;
}
