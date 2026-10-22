#include <mpv/ohcodec_terminal.h>
#include <dlfcn.h>
#include <pthread.h>
#include <stdatomic.h>
#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include <time.h>
#include <errno.h>
static atomic_int notices;static int token;
static void recv_record(const mpv_ohcodec_terminal_record*r,void*o){if(o!=&token||r->size!=sizeof(*r)||r->abi_version!=MPV_OHCODEC_TERMINAL_ABI_VERSION||r->platform_error!=-4)abort();atomic_fetch_add(&notices,1);}
static void *(*trigger)(void*);
int main(int argc,char **argv){if(argc!=3)return 64;void*h=dlopen(argv[1],RTLD_NOW|RTLD_LOCAL);if(!h){puts(dlerror());return 2;}
 uint32_t(*ver)(void)=dlsym(h,"mpv_ohcodec_terminal_api_version");int(*reg)(const mpv_ohcodec_terminal_config*)=dlsym(h,"mpv_ohcodec_terminal_register");int(*en)(void)=dlsym(h,"mpv_ohcodec_terminal_enable");int(*snap)(mpv_ohcodec_terminal_record*)=dlsym(h,"mpv_ohcodec_terminal_snapshot");
 if(!ver||!reg||!en||!snap){puts("FAIL required public ABI symbols missing");return 3;}
 if(ver()!=MPV_OHCODEC_TERMINAL_ABI_VERSION)return 4;
 trigger=dlsym(h,"test_enter");void(*fail)(int)=dlsym(h,"test_thread_failure");
 mpv_ohcodec_terminal_config c={.size=sizeof(c),.abi_version=MPV_OHCODEC_TERMINAL_ABI_VERSION,.handler=recv_record,.opaque=&token};
 mpv_ohcodec_terminal_record r={.size=sizeof(r),.abi_version=MPV_OHCODEC_TERMINAL_ABI_VERSION};const char*m=argv[2];
 if(!strcmp(m,"invalid")){
  uint32_t *shortbuf=malloc(8);shortbuf[0]=8;shortbuf[1]=MPV_OHCODEC_TERMINAL_ABI_VERSION;
  if(reg((const mpv_ohcodec_terminal_config*)shortbuf)>=0||snap((mpv_ohcodec_terminal_record*)shortbuf)>=0)return 9;free(shortbuf);
  if(reg(NULL)>=0||snap(NULL)>=0||en()>=0)return 10;
  c.size=8;if(reg(&c)>=0)return 11;c.size=sizeof(c);c.abi_version=0;if(reg(&c)>=0)return 12;c.abi_version=0x20000;if(reg(&c)>=0)return 13;c.abi_version=MPV_OHCODEC_TERMINAL_ABI_VERSION;c.reserved[0]=1;if(reg(&c)>=0)return 14;c.reserved[0]=0;c.handler=NULL;if(reg(&c)>=0)return 15;c.handler=recv_record;
  r.size=8;if(snap(&r)>=0)return 16;r.size=sizeof(r);r.abi_version=0x10001;if(snap(&r)>=0)return 17;r.abi_version=MPV_OHCODEC_TERMINAL_ABI_VERSION;r.reserved[3]=1;if(snap(&r)>=0)return 18;r.reserved[3]=0;
  if(reg(&c)||en()||snap(&r)!=0)return 19;
 }else if(!strcmp(m,"retry")){fail(1);if(reg(&c)>=0||en()>=0)return 20;fail(0);if(reg(&c)||en()||reg(&c)>=0)return 21;
 }else if(!strcmp(m,"future-copy")){
  struct{mpv_ohcodec_terminal_config c;uint64_t tail;}big={.c=c,.tail=0x12345678};big.c.size=sizeof(big);if(reg(&big.c)||en())return 30;
  memset(&big,0,sizeof(big)); /* callback/opaque copied, not borrowed stack options */
  pthread_t t;pthread_create(&t,NULL,trigger,NULL);struct timespec d={0,50000000};nanosleep(&d,NULL);
  struct{mpv_ohcodec_terminal_record r;uint64_t tail;}out={.r=r,.tail=0xabcddcba};out.r.size=sizeof(out);
  if(snap(&out.r)!=1||out.tail!=0xabcddcba||out.r.size!=sizeof(r)||out.r.platform_error!=-4||atomic_load(&notices)!=1)return 31;
  mpv_ohcodec_terminal_record again=r;if(snap(&again)!=1||memcmp(&again,&out.r,sizeof(r)))return 32;
 }else return 65;
 puts("PASS public ABI");return 0;}
