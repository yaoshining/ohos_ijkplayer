/* 独立 normal 产品原型；宿主必须先注册进程寿命接管器。 */
#ifndef MP_OHCODEC_TERMINAL_H
#define MP_OHCODEC_TERMINAL_H
#include <stdbool.h>
#include <stdint.h>
enum mp_ohcodec_terminal_stage { MP_OHCODEC_TERMINAL_DRAIN=1, MP_OHCODEC_TERMINAL_RETAINED=2, MP_OHCODEC_TERMINAL_LATE=3 };
struct mp_ohcodec_terminal_record {
    int platform_error;
    int stage;
    uintptr_t owner_tag; /* 仅数值身份，不允许接收者解引用。 */
};
typedef void (*mp_ohcodec_terminal_handler)(const struct mp_ohcodec_terminal_record *,void *);
/* 一次注册；成功后不得卸载代码/释放 opaque，直至进程结束。无注销API。 */
int mp_ohcodec_terminal_register(mp_ohcodec_terminal_handler handler,void *opaque);
bool mp_ohcodec_terminal_enable(void);
bool mp_ohcodec_terminal_can_start(void);
/* permit线性化发放；终局不等待旧permit；完成时false表示不得发布会话。 */
bool mp_ohcodec_terminal_begin_creation(void);
bool mp_ohcodec_terminal_end_creation(void);
bool mp_ohcodec_terminal_snapshot(struct mp_ohcodec_terminal_record *out);
/* 受保护平台资源必须先通过 can_start；此终局只等待宿主有限退出。 */
void mp_ohcodec_terminal_enter(int error,int stage,uintptr_t owner_tag);
#endif
