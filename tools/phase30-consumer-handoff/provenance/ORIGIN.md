# 来源与许可

基线提交为 6520a29a83dc59f0bec57bf35684ba6f79c2fb43。FFmpeg/mpv 继承该阶段锁定输入和历史 OHCodec 补丁，本轮只增加独立 TRACE/TEST 仪表。来源哈希由 source-index.json 绑定，实际目标依赖锁、宏、编译器命令与本地 HAP 另封存。

ffmpeg-input 为 A TRACE 源，ffmpeg-test-input 为 B TRACE+TEST 源；input-package 与 input-package-concurrency 是对应 mpv 原始完整 translation units（只收录本轮涉及文件，不称整个源码分发）。第三方文件保留原版权头及 licenses/ 的 GPL/LGPL 原文。应用 FFmpeg/mpv 头与许可证同源。自有媒体及字体未上传；字体许可证文本保留。

CI runner、函数提取测试继承已审阶段并在本轮适配，来源文件原算法不改写；宿主适配仅替代 SDK 调用和 OS 线程接口，真实目标 TID 使用锁定 OHOS SDK pthread_gettid_np。测试使用 Linux gettid/macOS pthread_threadid_np；不是 pthread_t 地址。
