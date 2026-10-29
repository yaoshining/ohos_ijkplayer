/* Process-lifetime configuration. All lifecycle operations use rt_lock.
 * Immutable strings are atomically published and never freed after publication. */
#include "smb_runtime_internal.h"
#include <errno.h>
#include <fcntl.h>
#include <limits.h>
#include <pthread.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/stat.h>
#include <unistd.h>

static pthread_mutex_t rt_mutex = PTHREAD_MUTEX_INITIALIZER;
static __thread int rt_inside;
static int rt_started, rt_failed;
static unsigned long rt_live;
struct rt_values { char *input[4]; char *paths[11]; };
static struct rt_values *rt_published;
static const char *const rt_keys[11] = {"CONFIGFILE", "PRIVATE_DIR", "STATEDIR", "LOCKDIR", "CACHEDIR", "CODEPAGEDIR", "LMHOSTSFILE", "MODULESDIR", "LOGFILEBASE", "PIDDIR", "SMB_PASSWD_FILE"};
static const int rt_root[11] = {0,1,1,1,2,3,3,3,1,1,1};
static const char *const rt_suffix[11] = {"","/private","/state","/lock","","/codepages","/etc/lmhosts","/modules","/log","/run","/private/smbpasswd"};
#ifdef RT_TESTING
static int rt_alloc_after = -1;
void rt_test_fail_alloc_after(int n) { rt_alloc_after = n; }
#endif
static void *rt_alloc(size_t n) {
#ifdef RT_TESTING
    if (rt_alloc_after == 0) { errno = ENOMEM; return NULL; }
    if (rt_alloc_after > 0) --rt_alloc_after;
#endif
    void *p = calloc(1,n); if (!p) errno=ENOMEM; return p;
}
static char *rt_copy(const char *a, const char *b) {
    size_t n = strlen(a)+strlen(b)+1; char *p=rt_alloc(n);
    if (p) { strcpy(p,a); strcat(p,b); } return p;
}
int rt_lock(void) {
    if (rt_inside) { errno=EDEADLK; return -1; }
    int e=pthread_mutex_lock(&rt_mutex); if(e){errno=e;return -1;}
    rt_inside=1; return 0;
}
void rt_unlock(void) { rt_inside=0; pthread_mutex_unlock(&rt_mutex); }
int rt_begin(void) {
    if (rt_failed) {errno=EIO;return -1;}
    rt_started=1; return 0;
}
void rt_fail(void) { rt_failed=1; }
void rt_add_context(void) { ++rt_live; }
int rt_remove_context(void) { if (!rt_live) {errno=EINVAL;return 0;} return --rt_live==0; }
const char *rt_dyn(const char *name) {
    struct rt_values *p=__atomic_load_n(&rt_published,__ATOMIC_ACQUIRE);
    if (!p) return NULL;
    for (size_t i=0;i<11;++i) if (!strcmp(name,rt_keys[i])) return p->paths[i];
    return NULL;
}
const char *rt_parameter(const char *name) {
    static const char *const names[]={"private dir","state directory","lock directory","cache directory","pid directory","smb passwd file"};
    static const char *const keys[]={"PRIVATE_DIR","STATEDIR","LOCKDIR","CACHEDIR","PIDDIR","SMB_PASSWD_FILE"};
    for(size_t i=0;i<6;++i) if(!strcmp(name,names[i])) return rt_dyn(keys[i]);
    return NULL;
}
static int rt_syntax(const char *p) {
    if(!p || p[0]!='/' || !p[1] || strlen(p)>4095 || p[strlen(p)-1]=='/' || strstr(p,"//") || strstr(p,"/../") || strstr(p,"/./") || !strcmp(p+strlen(p)-2,"/.") || (strlen(p)>=3 && !strcmp(p+strlen(p)-3,"/.."))) {errno=EINVAL;return -1;}
    for(const unsigned char *q=(const unsigned char*)p;*q;++q) if(*q<32 || *q==127 || *q=='%'){errno=EINVAL;return -1;}
    return 0;
}
static int rt_check(const char *p,int directory,int writable) {
    struct stat s; char canonical[PATH_MAX];
    if(rt_syntax(p))return -1;
    if(!realpath(p,canonical))return -1;
    if(strcmp(p,canonical)){errno=EINVAL;return -1;}
    if(stat(p,&s))return -1;
    if(directory ? !S_ISDIR(s.st_mode) : !S_ISREG(s.st_mode)){errno=directory?ENOTDIR:EINVAL;return -1;}
    int mode=R_OK|(directory?X_OK:0)|(writable?W_OK:0);
    if(!(s.st_mode&0444) || (directory && !(s.st_mode&0111)) || (writable && !(s.st_mode&0222))){errno=EACCES;return -1;}
    return faccessat(AT_FDCWD,p,mode,AT_EACCESS);
}
static void rt_discard(struct rt_values *p) {
    if(!p)return;
    for(size_t i=0;i<4;++i)free(p->input[i]);
    for(size_t i=0;i<11;++i)free(p->paths[i]);
    free(p);
}
static int rt_existing(const char *const *input) {
    if(rt_failed){errno=EIO;return -1;}
    struct rt_values *p=rt_published;
    if(p){for(size_t i=0;i<4;++i)if(strcmp(input[i],p->input[i])){errno=EBUSY;return -1;}return 1;}
    if(rt_started){errno=EBUSY;return -1;}
    return 0;
}
int ohcodec_smb_runtime_configure_internal(const struct ohcodec_smb_runtime_v1 *c) {
    if(!c || c->struct_size!=sizeof(*c)){errno=EINVAL;return -1;}
    const char *input[]={c->config_file,c->state_root,c->cache_root,c->resource_root};
    for(size_t i=0;i<4;++i)if(rt_syntax(input[i]))return -1;
    if(rt_lock())return -1;
    int old=rt_existing(input);rt_unlock();if(old)return old>0?0:-1;
    struct rt_values *p=rt_alloc(sizeof(*p));if(!p)return -1;
    for(size_t i=0;i<4;++i){p->input[i]=rt_copy(input[i],"");if(!p->input[i])goto fail;}
    for(size_t i=0;i<11;++i){p->paths[i]=rt_copy(input[rt_root[i]],rt_suffix[i]);if(!p->paths[i] || rt_syntax(p->paths[i]))goto fail;}
    if(rt_check(input[0],0,0) || rt_check(input[1],1,1) || rt_check(input[2],1,1) || rt_check(input[3],1,0))goto fail;
    for(size_t i=1;i<=3;++i)if(rt_check(p->paths[i],1,1))goto fail;
    if(rt_lock())goto fail;
    old=rt_existing(input);
    if(!old)__atomic_store_n(&rt_published,p,__ATOMIC_RELEASE);
    rt_unlock();if(!old)return 0;
    rt_discard(p);return old>0?0:-1;
fail: {int e=errno;rt_discard(p);errno=e;return -1;}
}

int rt_validate_current(void) {
    struct rt_values *p=__atomic_load_n(&rt_published,__ATOMIC_ACQUIRE);
    if(!p)return 0;
    if(rt_check(p->input[0],0,0) || rt_check(p->input[1],1,1) || rt_check(p->input[2],1,1) || rt_check(p->input[3],1,0))return -1;
    for(size_t i=1;i<=3;++i)if(rt_check(p->paths[i],1,1))return -1;
    return 0;
}
