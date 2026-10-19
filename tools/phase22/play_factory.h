#pragma once
#include <mpv/client.h>
struct p22_play_config {const char *surface;int width,height,vulkan,hardware;const char *fonts,*cache;int rgba8;};
int p22_play_create(const p22_play_config*,mpv_handle**);
