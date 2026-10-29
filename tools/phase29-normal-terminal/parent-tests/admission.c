/* 平台仅桩替代，owner init 函数逐字来自候选源；normal 宏配置。 */
#include <stdio.h>
#include <stdlib.h>
#include <stdarg.h>
#include <stdatomic.h>
#include <stdbool.h>
#include <stdint.h>
#include <inttypes.h>
#include <pthread.h>
#include <errno.h>
#include <string.h>
#include <time.h>
#include <unistd.h>
#include "ohcodec_terminal.h"
static void event(const char *fmt,...) { va_list a;va_start(a,fmt);vfprintf(stdout,fmt,a);va_end(a);fputc('\n',stdout);fflush(stdout); }
#include "terminal_adapter.h"
typedef void *pl_gpu; typedef void *pl_vulkan; typedef struct {int x;} OH_NativeImage;
struct ra {int applicable;};struct ra_ctx {struct ra *ra;};
struct ohcodec_surface {OH_NativeImage *image;void *window;};
struct ohcodec_priv {struct ohcodec_surface *surface;void *interop_owner_priv;const void *interop;};
struct ra_hwdec {struct ohcodec_priv *priv;struct ra_ctx *ra_ctx;};
struct vk_owner {struct ohcodec_surface surface;pl_vulkan vk;};
static const int interop;
static atomic_int creates,create_started,allow_create,returned,cleanups;
static int block_create,fail_native;
#define MP_ERR(o,...) event(__VA_ARGS__)
#define MP_INFO(o,...) event(__VA_ARGS__)
#define MP_VERBOSE(o,...) ((void)0)
#define talloc_zero(ctx,type) calloc(1,sizeof(type))
#define talloc_free(p) do {atomic_fetch_add(&cleanups,1);free(p);} while(0)
#define VK_OHOS_EXTERNAL_MEMORY_EXTENSION_NAME "memory"
#define VK_OHOS_NATIVE_BUFFER_EXTENSION_NAME "buffer"
#define NATIVEBUFFER_USAGE_HW_TEXTURE 1
#define NATIVE_ERROR_OK 0
static pl_gpu ra_pl_get(struct ra *r) {return r->applicable?r:NULL;}
static pl_vulkan pl_vulkan_get(pl_gpu g) {return g;}
static bool has_extension(pl_vulkan v,const char *n) {return v!=NULL;}
static int64_t p27_monotonic_us(void) {return 1;}
static OH_NativeImage *OH_ConsumerSurface_Create(void) {
 atomic_fetch_add(&creates,1);atomic_store(&create_started,1);event("EVENT owner-platform-create");
 while(block_create&&!atomic_load(&allow_create)){struct timespec d={0,1000000};nanosleep(&d,NULL);}
 return fail_native?NULL:calloc(1,sizeof(OH_NativeImage));
}
static int OH_ConsumerSurface_SetDefaultUsage(OH_NativeImage *p,int x) {return 0;}
static bool ohcodec_surface_init(struct ohcodec_surface *s,OH_NativeImage *i) {s->image=i;s->window=i;return true;}
static void OH_NativeImage_Destroy(OH_NativeImage **i) {atomic_fetch_add(&cleanups,1);free(*i);*i=NULL;}
#include "actual-owner-init.inc"
static struct ra ra={1};static struct ra_ctx ctx={&ra};static struct ohcodec_priv priv;static struct ra_hwdec hw={&priv,&ctx};
static void *init_thread(void *unused) {bool ok=ohcodec_interop_pl_init(&hw);atomic_store(&returned,1);event("EVENT owner-init-return ok=%d",ok);return NULL;}
static void *fault_thread(void *unused) {mp_ohcodec_terminal_enter(-4,MP_OHCODEC_TERMINAL_DRAIN,123);return NULL;}
int main(int argc,char **argv) {
 if(argc!=2)return 64;const char *m=argv[1];
 if(!strcmp(m,"unregistered")||!strcmp(m,"register-failed")) {
  if(!strcmp(m,"register-failed")){adapter_thread_fail=1;if(mp_ohcodec_terminal_register(adapter_callback,&adapter_notifications)==0)return 1;}
  bool ok=ohcodec_interop_pl_init(&hw);return ok||atomic_load(&creates)||priv.surface?1:0;
 }
 if(!strcmp(m,"non-vulkan")){ra.applicable=0;return ohcodec_interop_pl_init(&hw)||atomic_load(&creates)?1:0;}
 adapter_start();
 if(!strcmp(m,"normal")||!strcmp(m,"native-failed")) {
  fail_native=!strcmp(m,"native-failed");bool ok=ohcodec_interop_pl_init(&hw);
  if(ok==fail_native||atomic_load(&creates)!=1||!mp_ohcodec_terminal_can_start())return 1;
  return 0;
 }
 block_create=1;pthread_t a,b;pthread_create(&a,NULL,init_thread,NULL);
 while(!atomic_load(&create_started)){struct timespec d={0,1000000};nanosleep(&d,NULL);}
 pthread_create(&b,NULL,fault_thread,NULL);
 struct mp_ohcodec_terminal_record rec;while(!mp_ohcodec_terminal_snapshot(&rec)){struct timespec d={0,1000000};nanosleep(&d,NULL);}
 if(mp_ohcodec_terminal_begin_creation())return 1;
 event("EVENT blocked-create-terminal-visible error=%d new-permit=denied",rec.platform_error);
 if(!strcmp(m,"inflight-finishes")){atomic_store(&allow_create,1);struct timespec d={0,30000000};nanosleep(&d,NULL);}
 if(atomic_load(&returned)||priv.surface||atomic_load(&cleanups))return 1;
 event("EVENT inflight-owner-unpublished returned=0 surface=0 cleanups=0");
 for(;;){struct timespec d={0,1000000};nanosleep(&d,NULL);}
}
