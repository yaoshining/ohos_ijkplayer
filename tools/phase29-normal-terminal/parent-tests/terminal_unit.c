#define _POSIX_C_SOURCE 200809L
#include <stdio.h>
#include <stdlib.h>
#include <stdatomic.h>
#include <pthread.h>
#include <errno.h>
#include <string.h>
#include <time.h>
#include "ohcodec_terminal.h"
static int fail_create;
static atomic_int notices;
int probe_thread_create(pthread_t *t,const pthread_attr_t *a,void *(*f)(void *),void *p) { return fail_create ? EAGAIN : pthread_create(t,a,f,p); }
static void receiver(const struct mp_ohcodec_terminal_record *r,void *p) { if(p!=&notices)abort();atomic_fetch_add(&notices,1); }
static void *reg(void *p) { long *r=p;*r=mp_ohcodec_terminal_register(receiver,&notices);return NULL; }
static void *fault(void *p) { mp_ohcodec_terminal_enter(-4,MP_OHCODEC_TERMINAL_DRAIN,(uintptr_t)p);return NULL; }
int main(int argc,char **argv) {
 if(argc!=2)return 64;
 if(!strcmp(argv[1],"unregistered"))return mp_ohcodec_terminal_enable()||mp_ohcodec_terminal_can_start()?1:0;
 if(!strcmp(argv[1],"registration-failure")) { fail_create=1;int r=mp_ohcodec_terminal_register(receiver,&notices);return r==0||mp_ohcodec_terminal_enable()||mp_ohcodec_terminal_can_start()?1:0; }
 if(!strcmp(argv[1],"concurrent-register")) {
  pthread_t a,b;long x=0,y=0;pthread_create(&a,NULL,reg,&x);pthread_create(&b,NULL,reg,&y);pthread_join(a,NULL);pthread_join(b,NULL);
  if((x==0)+(y==0)!=1||!mp_ohcodec_terminal_enable())return 1;
  return mp_ohcodec_terminal_register(receiver,&notices)==0?1:0;
 }
 if(mp_ohcodec_terminal_register(receiver,&notices)||!mp_ohcodec_terminal_enable()||!mp_ohcodec_terminal_can_start())return 1;
 pthread_t a,b;pthread_create(&a,NULL,fault,(void*)11);pthread_create(&b,NULL,fault,(void*)22);
 struct timespec d={0,50000000};nanosleep(&d,NULL);
 struct mp_ohcodec_terminal_record r,s;
 if(!mp_ohcodec_terminal_snapshot(&r)||!mp_ohcodec_terminal_snapshot(&s)||memcmp(&r,&s,sizeof(r))||r.platform_error!=-4||atomic_load(&notices)!=1||mp_ohcodec_terminal_can_start())return 1;
 printf("PASS concurrent-first-writer notices=1 owner=%lu error=%d\n",(unsigned long)r.owner_tag,r.platform_error);return 0;
}
