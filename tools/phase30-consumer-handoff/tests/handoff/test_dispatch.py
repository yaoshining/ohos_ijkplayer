from pathlib import Path
import sys,hashlib,json,subprocess
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'lifecycle'))
from extract import find_body
r=Path(__file__).resolve().parents[2]; src=r/'input-package-concurrency/sources/mpv/misc/dispatch.c';s=src.read_text();out=Path(sys.argv[1]);out.mkdir(parents=True,exist_ok=False)
parts=[]
for marker in ['void mp_dispatch_lock(struct mp_dispatch_queue *queue)','void mp_dispatch_unlock(struct mp_dispatch_queue *queue)']:
 a,b=find_body(s,marker);parts.append(s[a:b])
observe=s[s.index('static atomic_uint_fast64_t p30_wait_tids'):s.index('#endif',s.index('static atomic_uint_fast64_t p30_wait_tids'))]
# Host OS TID adapter only; actual target observer gets pthread_gettid_np.
pre='''#include <pthread.h>
#include <stdint.h>
#include <stdatomic.h>
#include <assert.h>
#include <stdbool.h>
#include <stdio.h>
#include <time.h>
#define MP_OHCODEC_HANDOFF_TEST 1
#define mp_assert assert
#define mp_mutex_lock pthread_mutex_lock
#define mp_mutex_unlock pthread_mutex_unlock
#define mp_cond_wait pthread_cond_wait
#define mp_cond_broadcast pthread_cond_broadcast
#define mp_thread_id_equal pthread_equal
#define mp_thread_current_id pthread_self
static int enters;
#if defined(__linux__)
#include <unistd.h>
#include <sys/syscall.h>
static uint64_t os_tid(pthread_t t){(void)t;return syscall(SYS_gettid);}
#else
static uint64_t os_tid(pthread_t t){(void)t;uint64_t id=0;pthread_threadid_np(NULL,&id);return id;}
#endif
#define pthread_gettid_np os_tid
struct mp_dispatch_queue {pthread_mutex_t lock;pthread_cond_t cond;bool in_process,locked,locked_explicit;pthread_t in_process_thread_id,locked_explicit_thread_id;size_t lock_requests;void(*onlock_fn)(void*);void*onlock_ctx;void(*wakeup_fn)(void*);void*wakeup_ctx;};
'''
# Count observation invocations only, not rewrite dispatch algorithm.
observe=observe.replace('uint64_t tid=(uint64_t)pthread_gettid_np(pthread_self());','enters++;uint64_t tid=(uint64_t)pthread_gettid_np(pthread_self());')
post='''
static struct mp_dispatch_queue q={.lock=PTHREAD_MUTEX_INITIALIZER,.cond=PTHREAD_COND_INITIALIZER};
static void *worker(void*x){(void)x;mp_dispatch_lock(&q);mp_dispatch_unlock(&q);return NULL;}
int main(void){uint64_t ids[32];q.in_process=true;q.in_process_thread_id=(pthread_t)0;mp_dispatch_lock(&q);mp_dispatch_unlock(&q);assert(enters==0);q.in_process=false;pthread_t t;pthread_create(&t,NULL,worker,NULL);int found=0;for(int i=0;i<500;i++){if(mpv_ohcodec_handoff_test_waiting(ids,32)==1){found=1;break;}struct timespec n={0,1000000};nanosleep(&n,NULL);}assert(found&&enters==1);pthread_mutex_lock(&q.lock);q.in_process=true;pthread_cond_broadcast(&q.cond);pthread_mutex_unlock(&q.lock);pthread_join(t,NULL);assert(mpv_ohcodec_handoff_test_waiting(ids,32)==0);q.in_process=true;q.locked=true;pthread_create(&t,NULL,worker,NULL);found=0;for(int i=0;i<500;i++){if(mpv_ohcodec_handoff_test_waiting(ids,32)==1){found=1;break;}struct timespec n={0,1000000};nanosleep(&n,NULL);}assert(found&&enters==2);pthread_mutex_lock(&q.lock);q.locked=false;pthread_cond_broadcast(&q.cond);pthread_mutex_unlock(&q.lock);pthread_join(t,NULL);assert(mpv_ohcodec_handoff_test_waiting(ids,32)==0);puts("PASS actual-dispatch fast/no-observer blocked/visible unlock/cleared");}
'''
(out/'test.c').write_text(pre+observe+'\n'+'\n'.join(parts)+post)
cmd=['clang','-std=c11','-D_GNU_SOURCE','-pthread',str(out/'test.c'),'-o',str(out/'test')];c=subprocess.run(cmd,capture_output=True,text=True,timeout=30);(out/'compile.log').write_text(c.stdout+c.stderr);result={'sourceSHA':hashlib.sha256(src.read_bytes()).hexdigest(),'compileCommand':cmd,'compileExit':c.returncode,'accepted':False}
if c.returncode==0:
 p=subprocess.run([str(out/'test')],capture_output=True,text=True,timeout=5);(out/'run.log').write_text(p.stdout+p.stderr);result.update(exit=p.returncode,accepted=p.returncode==0)
(out/'results.json').write_text(json.dumps(result,indent=2)+'\n');print(result);sys.exit(not result['accepted'])
