/* 仅历史诊断 Flex 的 Linux 宿主编译；实现来自固定容器中的 libbsd。 */
#ifndef HX509_LINUX_FLEX_COMPAT_H
#define HX509_LINUX_FLEX_COMPAT_H
#include <stddef.h>
#ifndef __dead2
#define __dead2 __attribute__((__noreturn__))
#endif
#ifdef __cplusplus
extern "C" {
#endif
size_t strlcpy(char *, const char *, size_t);
size_t strlcat(char *, const char *, size_t);
#ifdef __cplusplus
}
#endif
#endif
