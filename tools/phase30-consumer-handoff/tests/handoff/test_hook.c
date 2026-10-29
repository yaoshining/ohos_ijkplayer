#include <assert.h>
#include <pthread.h>
#include <stdio.h>
#include <time.h>
#include "ohcodec_handoff_test.h"
static void *callback(void *unused){(void)unused;p30_handoff_hold(42,1);return NULL;}
int main(void){
 assert(av_ohcodec_handoff_test_arm(42)==0);
 assert(av_ohcodec_handoff_test_arm(42)!=0);
 p30_handoff_before_restart(42,1);
 pthread_t t;assert(!pthread_create(&t,NULL,callback,NULL));
 struct p30_handoff_snapshot s={0};
 for(int i=0;i<500;i++){av_ohcodec_handoff_test_snapshot(&s);if(s.state==3)break;struct timespec n={0,1000000};nanosleep(&n,NULL);}
 assert(s.state==3&&s.decoder==42&&s.callback_tid>0);
 p30_handoff_close_wait(41);av_ohcodec_handoff_test_snapshot(&s);assert(s.state==3);
 p30_handoff_close_wait(42);av_ohcodec_handoff_test_snapshot(&s);assert(s.state==4&&s.close_tid>0);
 assert(!av_ohcodec_handoff_test_release());pthread_join(t,NULL);av_ohcodec_handoff_test_snapshot(&s);assert(s.state==6);p30_handoff_close_wait(42);av_ohcodec_handoff_test_snapshot(&s);assert(s.state==6);atomic_store(&p30_state,7);p30_handoff_close_wait(42);av_ohcodec_handoff_test_snapshot(&s);assert(s.state==7);puts("PASS held-after-admit close-observation release");
}
