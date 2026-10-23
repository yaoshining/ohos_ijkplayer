# 输入与约束研究

Phase30 A: mpv SHA 1a469850c99635671281ddadc3c35e65121efda3da5382745cc3c33c8ddaaa31；libavcodec SHA 62331a15718a231f323ca0e8957272b7b1fc3eb48bf1e91d85a86760af15652a。实际宏证据为phase30 evidence/final-target-bindings.json，A为TRACE=true其余false。B是TEST变体，不用于本轮。

Phase25 nas-long-01 曾有3603.64s有效连续窗口；这不是本轮新组合证据。timeline已有同步调用配对、心跳、UIAbility/Stage/window事件，优先复用；旧52分钟采样空档根因未解决。

历史外部凭据路径不存在；本轮private/credentials.json空模板已创建，用户随后确认已填写并授权程序读取。NAS预检通过，片源实际1920x800/H264 8bit/BT709 SDR；仅用别名nas-media-01。禁止搜索钥匙串或广泛凭据。设备192.168.3.85:5555初次devecocli无活动设备，仅重连网络调试后Connected；未改变系统设置。
