/* 宿主测试adapter，不是现有Player/TV接入。测试子进程自行结束。 */
#include "ohcodec_terminal.h"
static int adapter_thread_fail, adapter_callback_hang, adapter_skip_callback;
static atomic_int adapter_notifications;
int probe_thread_create(pthread_t *t, const pthread_attr_t *a, void *(*fn)(void *), void *p) {
    if (adapter_thread_fail) return EAGAIN;
    return pthread_create(t,a,fn,p);
}
static void adapter_callback(const struct mp_ohcodec_terminal_record *r, void *opaque) {
    if (opaque != &adapter_notifications) _Exit(92);
    atomic_fetch_add(&adapter_notifications,1);
    event("EVENT terminal-notification count=%d error=%d stage=%d", atomic_load(&adapter_notifications), r->platform_error, r->stage);
    if (adapter_skip_callback) return;
    if (adapter_callback_hang) for (;;) { struct timespec d={0,1000000};nanosleep(&d,NULL); }
    event("EVENT app-simulated-fault-prompt");
    event("EVENT app-simulated-keep-screen-off");
    event("EVENT app-uses-cached-progress-only");
}
static void *adapter_deadline(void *unused) {
    struct mp_ohcodec_terminal_record r;
    for (;;) {
        if (mp_ohcodec_terminal_snapshot(&r)) {
            struct timespec d={0,150000000};nanosleep(&d,NULL);
            event("EVENT terminal-ready error=%d stage=%d notices=%d admission=%d", r.platform_error, r.stage, atomic_load(&adapter_notifications), mp_ohcodec_terminal_can_start());
            static const char msg[]="EVENT app-deadline-exit cached-progress-only\n";
            write(STDOUT_FILENO,msg,sizeof(msg)-1);
            _Exit(86);
        }
        struct timespec d={0,1000000};nanosleep(&d,NULL);
    }
}
static void adapter_start(void) {
    if (mp_ohcodec_terminal_register(adapter_callback,&adapter_notifications) ||
        !mp_ohcodec_terminal_enable()) _Exit(93);
    pthread_t t;
    if (pthread_create(&t,NULL,adapter_deadline,NULL)) _Exit(94);
    pthread_detach(t);
}
