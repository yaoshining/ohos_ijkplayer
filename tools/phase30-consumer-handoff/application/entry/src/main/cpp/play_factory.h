#pragma once
#include <mpv/client.h>
struct p22_play_config {const char *surface;int width,height,vulkan,hardware;const char *fonts,*cache;int rgba8;bool privateMedia=false;const char *username=nullptr,*password=nullptr,*domain=nullptr;bool rgb10=false;const char *logFile=nullptr;bool preserveConsumer=false;};
int p22_play_create(const p22_play_config*,mpv_handle**);
