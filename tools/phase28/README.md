# Phase28 CI

固定 upstream FFmpeg，先应用 Phase27 portable patch，再应用 Phase28 `ohdec.c` 增量补丁；验证 Phase28 完整源集合后运行：
T005/T007/T012 mpv 真实函数 RED/GREEN、T008/T010 ohdec 真实函数 RED/GREEN、T011 实验宏/watchdog、T013 HDR/SEI/AnnexB/preference 回归。
只上传文本日志/JSON，不包含库、HAP、SDK、签名或媒体夹具。目标设备验收独立进行。
