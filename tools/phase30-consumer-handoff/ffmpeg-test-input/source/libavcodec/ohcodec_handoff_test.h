/* 仅独立测试变体：控制真实回调时序，不准入、不拒绝 producer。 */
#ifndef OHCODEC_HANDOFF_TEST_H
#define OHCODEC_HANDOFF_TEST_H
#include <pthread.h>
#include <stdint.h>
#include <stdatomic.h>
#include <time.h>
#include <errno.h>
#if defined(__linux__) && !defined(__OHOS__)
#include <unistd.h>
#include <sys/syscall.h>
#endif
struct p30_handoff_snapshot { uint64_t state, decoder, callback_tid, close_tid, epoch; };
int av_ohcodec_handoff_test_arm(uint64_t decoder);
int av_ohcodec_handoff_test_snapshot(struct p30_handoff_snapshot *s);
int av_ohcodec_handoff_test_release(void);
static pthread_mutex_t p30_lock = PTHREAD_MUTEX_INITIALIZER;
static pthread_cond_t p30_cond = PTHREAD_COND_INITIALIZER;
static atomic_uint_fast64_t p30_state, p30_decoder, p30_callback_tid, p30_close_tid, p30_epoch;
static int p30_released;
static uint64_t p30_tid(void) {
#ifdef __APPLE__
 uint64_t id=0; pthread_threadid_np(NULL,&id); return id;
#elif defined(__OHOS__)
 return pthread_gettid_np(pthread_self());
#elif defined(__linux__)
 return (uint64_t)syscall(SYS_gettid);
#else
#error unsupported real OS TID provider
#endif
}
static struct timespec p30_deadline(void){struct timespec t;clock_gettime(CLOCK_REALTIME,&t);t.tv_sec+=5;return t;}
__attribute__((visibility("default"))) int av_ohcodec_handoff_test_arm(uint64_t decoder){if(!decoder)return -1;uint_fast64_t zero=0;if(!atomic_compare_exchange_strong(&p30_state,&zero,8))return -1;atomic_store(&p30_decoder,decoder);atomic_store(&p30_state,1);return 0;}
__attribute__((visibility("default"))) int av_ohcodec_handoff_test_snapshot(struct p30_handoff_snapshot *s){if(!s)return -1;s->state=atomic_load(&p30_state);s->decoder=atomic_load(&p30_decoder);s->callback_tid=atomic_load(&p30_callback_tid);s->close_tid=atomic_load(&p30_close_tid);s->epoch=atomic_load(&p30_epoch);return 0;}
__attribute__((visibility("default"))) int av_ohcodec_handoff_test_release(void){pthread_mutex_lock(&p30_lock);p30_released=1;pthread_cond_broadcast(&p30_cond);pthread_mutex_unlock(&p30_lock);return 0;}
/* 只在实际 Flush 完成且重新开放 admit 后，使下一次真实 Start 回调可被保持。 */
static void p30_handoff_before_restart(uint64_t decoder,uint64_t epoch){pthread_mutex_lock(&p30_lock);if(atomic_load(&p30_state)==1 && atomic_load(&p30_decoder)==decoder){atomic_store(&p30_epoch,epoch);atomic_store(&p30_state,2);}pthread_mutex_unlock(&p30_lock);}
static void p30_handoff_hold(uint64_t decoder,uint64_t epoch){
 pthread_mutex_lock(&p30_lock);
 if(atomic_load(&p30_state)!=2 || atomic_load(&p30_decoder)!=decoder || atomic_load(&p30_epoch)!=epoch){pthread_mutex_unlock(&p30_lock);return;}
 atomic_store(&p30_callback_tid,p30_tid());atomic_store(&p30_state,3);pthread_cond_broadcast(&p30_cond);
 struct timespec limit=p30_deadline();while(!p30_released){if(pthread_cond_timedwait(&p30_cond,&p30_lock,&limit)==ETIMEDOUT){atomic_store(&p30_state,7);pthread_mutex_unlock(&p30_lock);return;}}
 atomic_store(&p30_state,6);pthread_mutex_unlock(&p30_lock);
}
static void p30_handoff_after_restart(uint64_t decoder){
 pthread_mutex_lock(&p30_lock);struct timespec limit=p30_deadline();
 while(atomic_load(&p30_state)==2 && atomic_load(&p30_decoder)==decoder){if(pthread_cond_timedwait(&p30_cond,&p30_lock,&limit)==ETIMEDOUT){atomic_store(&p30_state,7);break;}}
 pthread_mutex_unlock(&p30_lock);
}
static void p30_handoff_close_wait(uint64_t decoder){
 if(atomic_load(&p30_decoder)==decoder){uint_fast64_t held=3;atomic_store(&p30_close_tid,p30_tid());atomic_compare_exchange_strong(&p30_state,&held,4);}
}
#endif
