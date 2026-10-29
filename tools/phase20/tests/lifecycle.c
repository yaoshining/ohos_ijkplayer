#include "smb_runtime_internal.h"
#include <assert.h>
#include <errno.h>
#include <stdlib.h>
#include <string.h>
#include <pthread.h>
#include <sched.h>
typedef struct { int initialized; } SMBCCTX;
static int allocations, terminations, fail_new, fail_init, busy, recurse;
static int race_go, config_result, config_errno, observed_explicit;
static struct ohcodec_smb_runtime_v1 race_config;
static SMBCCTX *smbc_new_context_runtime_original(void) {
 if(fail_new){errno=ENOMEM;return NULL;} SMBCCTX *c=calloc(1,sizeof(*c));if(c)allocations++;return c;
}
static SMBCCTX *smbc_init_context_runtime_original(SMBCCTX *c){
 if(!c){errno=EBADF;return NULL;}
 if(recurse){assert(rt_lock()==-1 && errno==EDEADLK);}
 if(fail_init){errno=EINVAL;return NULL;}if(c->initialized)return NULL;c->initialized=1;return c;
}
static int smbc_free_context_runtime_original(SMBCCTX *c,int shutdown){
 (void)shutdown;if(!c){errno=EBADF;return 1;}if(busy){errno=EBUSY;return 1;}free(c);allocations--;return 0;
}
static void SMBC_module_terminate(void){assert(allocations==0);terminations++;}
#include "smb_context_wrappers.inc"
static void *worker(void *unused){(void)unused;SMBCCTX *c=smbc_new_context();assert(c);assert(smbc_init_context(c));assert(smbc_free_context(c,1)==0);return NULL;}
static void *configure_worker(void *unused){(void)unused;while(!__atomic_load_n(&race_go,__ATOMIC_ACQUIRE))sched_yield();config_result=ohcodec_smb_runtime_configure_internal(&race_config);config_errno=errno;return NULL;}
static void *create_worker(void *unused){(void)unused;while(!__atomic_load_n(&race_go,__ATOMIC_ACQUIRE))sched_yield();SMBCCTX *c=smbc_new_context();assert(c);observed_explicit=rt_dyn("CONFIGFILE")!=NULL;assert(smbc_init_context(c));assert(smbc_free_context(c,1)==0);return NULL;}
int main(int argc,char **argv){
 assert(argc==2 || argc==6);
 if(!strcmp(argv[1],"pending")){
  SMBCCTX *a=smbc_new_context(),*b=smbc_new_context();assert(a&&b);assert(smbc_init_context(b));assert(smbc_free_context(b,1)==0);assert(terminations==0);assert(smbc_init_context(a));assert(smbc_free_context(a,1)==0);assert(terminations==1);
 }else if(!strcmp(argv[1],"failures")){
  fail_new=1;assert(!smbc_new_context());fail_new=0;SMBCCTX *a=smbc_new_context(),*b=smbc_new_context();fail_init=1;assert(!smbc_init_context(a));assert(smbc_free_context(a,1)==0);assert(terminations==0);fail_init=0;assert(smbc_init_context(b));busy=1;assert(smbc_free_context(b,0)==1);assert(terminations==0);busy=0;assert(smbc_free_context(b,1)==0);assert(terminations==1);
 }else if(!strcmp(argv[1],"repeat")){
  for(int n=0;n<3;n++){SMBCCTX *c=smbc_new_context();assert(smbc_init_context(c));assert(!smbc_init_context(c));assert(smbc_free_context(c,1)==0);}assert(terminations==3);
 }else if(!strcmp(argv[1],"reentry")){recurse=1;worker(NULL);
 }else if(!strcmp(argv[1],"threads")){pthread_t t[12];for(int i=0;i<12;i++)assert(!pthread_create(t+i,NULL,worker,NULL));for(int i=0;i<12;i++)pthread_join(t[i],NULL);assert(allocations==0);
 }else if(!strcmp(argv[1],"create-config-race")){
  assert(argc==6);race_config=(struct ohcodec_smb_runtime_v1){sizeof(race_config),argv[2],argv[3],argv[4],argv[5]};pthread_t a,b;
  assert(!pthread_create(&a,NULL,configure_worker,NULL));assert(!pthread_create(&b,NULL,create_worker,NULL));__atomic_store_n(&race_go,1,__ATOMIC_RELEASE);pthread_join(a,NULL);pthread_join(b,NULL);
  assert((config_result==0 && observed_explicit) || (config_result==-1 && config_errno==EBUSY && !observed_explicit));assert(allocations==0);
 }else return 2;
 return 0;
}
