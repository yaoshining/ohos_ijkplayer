#ifndef P21_INTEGRATION_H
#define P21_INTEGRATION_H
#include <stddef.h>
typedef struct mpv_handle mpv_handle;
struct p21_config { const char *config_file, *state_root, *cache_root, *resource_root; };
struct p21_error { const char *stage; int code; };
int p21_validate(const struct p21_config *, struct p21_error *);
int p21_create(const struct p21_config *, mpv_handle **, struct p21_error *);
void p21_destroy(mpv_handle **);
#endif
