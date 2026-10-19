/* Real native Samba integration: no mock lp/gencache/context implementation. */
#include "includes.h"
#include "libsmbclient.h"
#include "lib/gencache.h"
#include "../../dynconfig/smb_runtime_internal.h"
#include <assert.h>
#include <pthread.h>
static int purge_reentry(SMBCCTX *c) { (void)c;assert(smbc_new_context()==NULL && errno==EDEADLK);return 0; }
static void *native_worker(void *unused) { (void)unused;SMBCCTX *c=smbc_new_context();assert(c);assert(smbc_init_context(c));assert(!smbc_free_context(c,1));return NULL; }
static void auth(const char *s,const char *h,char *w,int wl,char *u,int ul,char *p,int pl)
{ (void)s;(void)h;(void)w;(void)wl;(void)u;(void)ul;(void)p;(void)pl; }
static void paths(const char *state,const char *cache)
{
 char p[4096];
 snprintf(p,sizeof(p),"%s/private",state);assert(!strcmp(lp_private_dir(),p));
 snprintf(p,sizeof(p),"%s/state",state);assert(!strcmp(lp_state_directory(),p));
 snprintf(p,sizeof(p),"%s/lock",state);assert(!strcmp(lp_lock_directory(),p));
 snprintf(p,sizeof(p),"%s/run",state);assert(!strcmp(lp_pid_directory(),p));
 snprintf(p,sizeof(p),"%s/private/smbpasswd",state);assert(!strcmp(lp_smb_passwd_file(),p));
 assert(!strcmp(lp_cache_directory(),cache));
 assert(!strcmp(lp_workgroup(),"PHASE20"));
}
int main(int argc,char **argv)
{
 assert(argc==6);const char *test=argv[1];
 struct ohcodec_smb_runtime_v1 config={sizeof(config),argv[2],argv[3],argv[4],argv[5]};
 assert(geteuid()!=0);
 if(!strncmp(test,"unconfigured-",13)) {
  SMBCCTX *c=smbc_new_context();assert(c);assert(smbc_init_context(c));
  assert(!strcmp(lp_workgroup(),!strcmp(test,"unconfigured-home")?"WRONG_HOME":"WRONG_APPEND"));
  assert(ohcodec_smb_runtime_configure_internal(&config)==-1 && errno==EBUSY);assert(!smbc_free_context(c,1));
 } else {
 assert(ohcodec_smb_runtime_configure_internal(&config)==0);
 if(!strcmp(test,"posix-threads")) {
  smbc_thread_posix();pthread_t threads[8];for(int i=0;i<8;i++)assert(!pthread_create(&threads[i],NULL,native_worker,NULL));for(int i=0;i<8;i++)assert(!pthread_join(threads[i],NULL));
  native_worker(NULL);assert(ohcodec_smb_runtime_configure_internal(&config)==0);
 } else if(!strcmp(test,"parse-failure")) {
  assert(smbc_new_context()==NULL && errno==EIO);
  assert(smbc_new_context()==NULL && errno==EIO);
  assert(ohcodec_smb_runtime_configure_internal(&config)==-1 && errno==EIO);
 } else if(!strcmp(test,"legacy-null")) {
  /* Upstream rejects NULL auth callbacks during init, and frees its context. */
  assert(smbc_init(NULL,0)==-1 && errno==EINVAL);
  assert(ohcodec_smb_runtime_configure_internal(&config)==0);
  SMBCCTX *c=smbc_new_context();assert(c);assert(smbc_init_context(c));paths(argv[3],argv[4]);assert(!smbc_free_context(c,1));
 } else if(!strcmp(test,"legacy-auth")) {
  assert(smbc_init(auth,0)==0);paths(argv[3],argv[4]);assert(smbc_init(auth,0)==0);
 } else {
  SMBCCTX *a=smbc_new_context();assert(a);
  if(!strcmp(test,"pending")) {SMBCCTX *b=smbc_new_context();assert(b);assert(smbc_init_context(b));assert(!smbc_free_context(b,1));}
  if(!strcmp(test,"init-failure")) {smbc_setDebug(a,-1);assert(!smbc_init_context(a) && errno==EINVAL);assert(!smbc_free_context(a,1));a=smbc_new_context();assert(a);}
  assert(smbc_init_context(a));paths(argv[3],argv[4]);
  assert(smbc_setConfiguration(a,argv[2])==-1 && errno==EBUSY);
  if(!strcmp(test,"aliases")) {assert(lp_do_parameter(-1,"LOCK DIR","/must-not-win"));assert(lp_load_client_no_reinit(argv[2]));paths(argv[3],argv[4]);}
  if(!strcmp(test,"cache-denied")) {
   char lock[4096];snprintf(lock,sizeof(lock),"%s/lock",argv[3]);assert(chmod(lock,0500)==0);
   assert(!gencache_set("PHASE20_KEY","value",time(NULL)+60));assert(chmod(lock,0700)==0);
  } else if(!strcmp(test,"cache-write")) {
   char *value=NULL;time_t timeout;assert(gencache_set("PHASE20_KEY","value",time(NULL)+60));
   assert(gencache_get("PHASE20_KEY",NULL,&value,&timeout));assert(!strcmp(value,"value"));TALLOC_FREE(value);
  }
  if(!strcmp(test,"callback-reentry"))smbc_setFunctionPurgeCachedServers(a,purge_reentry);
  assert(!smbc_free_context(a,1));
  if(!strcmp(test,"last-free") || !strcmp(test,"pending")) {
   assert(ohcodec_smb_runtime_configure_internal(&config)==0);a=smbc_new_context();assert(a);assert(smbc_init_context(a));paths(argv[3],argv[4]);assert(!smbc_free_context(a,1));
  }
 }
 }
 FILE *maps=fopen("/proc/self/maps","r");assert(maps);char line[8192];while(fgets(line,sizeof(line),maps))fputs(line,stdout);fclose(maps);
 printf("PHASE20_PASS %s\n",test);return 0;
}
