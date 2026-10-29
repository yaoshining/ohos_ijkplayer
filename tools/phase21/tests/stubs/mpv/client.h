#ifndef MPV_STUB_H
#define MPV_STUB_H
typedef struct mpv_handle mpv_handle;
mpv_handle *mpv_create(void);
int mpv_set_option_string(mpv_handle *,const char *,const char *);
int mpv_initialize(mpv_handle *);
void mpv_terminate_destroy(mpv_handle *);
#endif
