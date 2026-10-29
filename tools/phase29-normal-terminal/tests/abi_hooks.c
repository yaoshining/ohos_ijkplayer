#include <pthread.h>
#include <errno.h>
#include <stdatomic.h>
#include "ohcodec_terminal.h"
static atomic_int failing;
__attribute__((visibility("default"))) void test_thread_failure(int x){atomic_store(&failing,x);}
int probe_thread_create(pthread_t*t,const pthread_attr_t*a,void*(*f)(void*),void*p){return atomic_load(&failing)?EAGAIN:pthread_create(t,a,f,p);}
__attribute__((visibility("default"))) void *test_enter(void *p){mp_ohcodec_terminal_enter(-4,MP_OHCODEC_TERMINAL_DRAIN,123);return 0;}
