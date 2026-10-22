/* 进程寿命终局管理：不借用 mpv/VO/log 对象，不自行终止宿主。 */
#define _POSIX_C_SOURCE 200809L
#include "ohcodec_terminal.h"
#include <pthread.h>
#include <stdatomic.h>
#include <errno.h>
#include <time.h>
#include <limits.h>
/* 0未注册，1注册中，2注册成功。无运行期注销，避免回调壳提前释放。 */
static atomic_int registration;
static atomic_bool enabled;
#define CLOSED (1u << (sizeof(unsigned)*CHAR_BIT-1))
static atomic_uint admission;
static pthread_mutex_t notification_lock=PTHREAD_MUTEX_INITIALIZER;
static pthread_cond_t notification_cond=PTHREAD_COND_INITIALIZER;
/* 0健康，1首次写者持有，2不可变record发布完成。 */
static atomic_int publication;
static struct mp_ohcodec_terminal_record record;
static mp_ohcodec_terminal_handler callback;
static void *callback_opaque;
static void pause_poll(void) { struct timespec t={0,1000000};nanosleep(&t,NULL); }
static void *notify_thread(void *unused) {
    (void)unused;
    pthread_mutex_lock(&notification_lock);
    while (atomic_load_explicit(&publication,memory_order_acquire)!=2)
        pthread_cond_wait(&notification_cond,&notification_lock);
    pthread_mutex_unlock(&notification_lock);
    callback(&record,callback_opaque);
    return NULL;
}
int mp_ohcodec_terminal_register(mp_ohcodec_terminal_handler handler,void *opaque) {
    if (!handler) return EINVAL;
    int expected=0;
    if (!atomic_compare_exchange_strong_explicit(&registration,&expected,1,memory_order_acq_rel,memory_order_acquire)) return EALREADY;
    callback=handler;callback_opaque=opaque;
    pthread_t thread;
    int rc=pthread_create(&thread,NULL,notify_thread,NULL);
    if(rc) {
        callback=NULL;callback_opaque=NULL;
        atomic_store_explicit(&registration,0,memory_order_release);
        return rc;
    }
    pthread_detach(thread);
    atomic_store_explicit(&registration,2,memory_order_release);
    return 0;
}
bool mp_ohcodec_terminal_enable(void) {
    if(atomic_load_explicit(&registration,memory_order_acquire)!=2 || atomic_load_explicit(&publication,memory_order_acquire)!=0) return false;
    atomic_store_explicit(&enabled,true,memory_order_release);
    return true;
}
bool mp_ohcodec_terminal_can_start(void) {
    return atomic_load_explicit(&enabled,memory_order_acquire) && atomic_load_explicit(&registration,memory_order_acquire)==2 && !(atomic_load_explicit(&admission,memory_order_acquire)&CLOSED);
}
bool mp_ohcodec_terminal_begin_creation(void) {
    if (!atomic_load_explicit(&enabled,memory_order_acquire) || atomic_load_explicit(&registration,memory_order_acquire)!=2) return false;
    unsigned v=atomic_load_explicit(&admission,memory_order_acquire);
    for (;;) {
        if ((v&CLOSED) || (v&~CLOSED)==CLOSED-1) return false;
        if (atomic_compare_exchange_weak_explicit(&admission,&v,v+1,memory_order_acq_rel,memory_order_acquire)) return true;
    }
}
bool mp_ohcodec_terminal_end_creation(void) {
    unsigned before=atomic_fetch_sub_explicit(&admission,1,memory_order_acq_rel);
    return !(before&CLOSED);
}
bool mp_ohcodec_terminal_snapshot(struct mp_ohcodec_terminal_record *out) {
    if(!out || atomic_load_explicit(&publication,memory_order_acquire)!=2) return false;
    *out=record;
    return true;
}
void mp_ohcodec_terminal_enter(int error,int stage,uintptr_t owner_tag) {
    atomic_fetch_or_explicit(&admission,CLOSED,memory_order_acq_rel);
    int expected=0;
    if(atomic_compare_exchange_strong_explicit(&publication,&expected,1,memory_order_acq_rel,memory_order_acquire)) {
        record=(struct mp_ohcodec_terminal_record){.platform_error=error,.stage=stage,.owner_tag=owner_tag};
        atomic_store_explicit(&publication,2,memory_order_release);
        /* 发布不等待任何播放/创建锁；此锁仅由睡眠中的通知线程短持有。 */
        pthread_mutex_lock(&notification_lock);
        pthread_cond_signal(&notification_cond);
        pthread_mutex_unlock(&notification_lock);
    }
    /* 未再触碰平台、释放父级或调用宿主。外部接管器拥有退出权限。 */
    for(;;) pause_poll();
}
