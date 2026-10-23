#pragma once
#include <cstdint>
bool terminal_app_start(const char *root,const char *mode);
bool terminal_app_admit();
int terminal_app_state();
void terminal_app_mark_ui(int code);
void terminal_app_cache_progress(int64_t milliseconds);
int64_t terminal_app_cached_progress();
#ifdef TERMINAL_APP_HOST_TEST
void test_inject_terminal();
#endif
