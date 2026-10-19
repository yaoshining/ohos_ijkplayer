#pragma once
#include <string>
struct p22_smb_options {std::string url,user,password;};
inline bool p22_split_smb(const std::string &s,p22_smb_options &o){
 if(s.rfind("smb://",0)!=0)return false;
 for(unsigned char c:s)if(c<32||c==127)return false;
 auto at=s.find('@',6),colon=s.find(':',6),slash=s.find('/',6);
 if(at==std::string::npos||colon==std::string::npos||colon>=at||colon==6||slash==std::string::npos||slash<at||at+1==slash)return false;
 o.user=s.substr(6,colon-6);o.password=s.substr(colon+1,at-colon-1);o.url="smb://"+s.substr(at+1);return true;
}
