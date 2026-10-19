#pragma once
#include <string>
#include <vector>
inline std::string p22_redact(std::string s,const std::vector<std::string> &secrets){for(auto &word:secrets){if(word.empty())continue;size_t p=0;while((p=s.find(word,p))!=std::string::npos){s.replace(p,word.size(),"[redacted]");p+=10;}}size_t p=0;while((p=s.find("smb://",p))!=std::string::npos){size_t end=s.find_first_of(" \n\r\t",p);s.replace(p,end==std::string::npos?s.size()-p:end-p,"[SMB URL]");p+=9;}return s;}
