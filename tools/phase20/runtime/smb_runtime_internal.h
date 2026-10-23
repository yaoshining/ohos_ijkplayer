#ifndef OHCODEC_SMB_RUNTIME_INTERNAL_H
#define OHCODEC_SMB_RUNTIME_INTERNAL_H
#include "smb_runtime.h"
int ohcodec_smb_runtime_configure_internal(const struct ohcodec_smb_runtime_v1 *);
int rt_lock(void);
void rt_unlock(void);
int rt_begin(void);
int rt_validate_current(void);
void rt_fail(void);
void rt_add_context(void);
int rt_remove_context(void);
const char *rt_dyn(const char *);
const char *rt_parameter(const char *);
#endif
