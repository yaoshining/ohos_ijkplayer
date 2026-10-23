/* 先行应用adapter契约：专用子进程可有界退出，不调用任何mpv同步控制。 */
#include "terminal_adapter.h"
#include <thread>
#include <chrono>
#include <cstring>
#include <cstdlib>
int main(int n,char**v){if(n!=2)return 64;const char*m=v[1];
 if(!strcmp(m,"no-registration"))return terminal_app_start(getenv("APP_TEST_ROOT"),m)||terminal_app_admit()?1:0;
 if(!terminal_app_start(getenv("APP_TEST_ROOT"),!strcmp(m,"logger-hang")?"fault":m)||!terminal_app_admit())return 2;
 if(!strcmp(m,"healthy-repeat")){for(int i=0;i<2;i++){if(!terminal_app_admit())return 3;terminal_app_cache_progress(10+i);}std::this_thread::sleep_for(std::chrono::milliseconds(150));return terminal_app_state()!=0?4:0;}
 test_inject_terminal();
 if(!strcmp(m,"logger-hang"))for(;;)std::this_thread::sleep_for(std::chrono::milliseconds(10));
 for(int i=0;i<500;i++){if(terminal_app_state()){if(terminal_app_admit())return 5;if(terminal_app_cached_progress()!=0)return 6;}std::this_thread::sleep_for(std::chrono::milliseconds(10));}
 return 7;
}
