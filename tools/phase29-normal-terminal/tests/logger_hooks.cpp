#include <unistd.h>
#include <cstdlib>
#include <string>
#include <thread>
#include <chrono>
extern "C" ssize_t probe_write(int fd,const void *data,size_t n){
 const char *m=getenv("APP_TEST_MODE");
 if(m&&std::string(m)=="logger-hang"&&std::string((const char*)data,n).find("event=terminal-ready")!=std::string::npos)
  {const char marker[]="LOGGER_REAL_WRITE_BLOCKED\n";write(2,marker,sizeof(marker)-1);for(;;)std::this_thread::sleep_for(std::chrono::seconds(1));}
 return write(fd,data,n);
}
