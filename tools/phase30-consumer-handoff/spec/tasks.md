# 任务与实际状态

- [x] C001 校验旧封存、保护边界与源码；旧应用四项历史输入未独立封存已如实报告。
- [x] C002 Spec Kit prerequisites（NO_PERSIST）及 root 规格分析通过。
- [x] C003 观测/解析 RED、真实 FFmpeg 同步回归、去 Close 等待变异拒绝；A/B 解析夹具各 16 项。
- [x] C004 独立 TRACE/TEST 仪表与应用双请求线程；normal 终局策略保持。
- [x] C005 目标构建及 A02/B03 真机，实际源快照、编译器依赖、HAP 与映射身份绑定。
- [x] C006a root 原始设备/来源/清理独立复核。
- [ ] C006b 新 CI 文本包本地精确提交重放、最终边界、精确推送预览。
- [ ] C007 用户批准新 SHA 后才推送并运行 Ubuntu CI；本地 macOS 通过不可替代。

## 限定验收

A02：4 代 decoder、3 次同一 owner/NativeImage/consumer Surface 的顺序交接；TRACE 开，TEST/DIAGNOSTIC 关。
B03：单个 mpv 实例，真实 callback 已获 admit，真实 Close 等待 active；两条不同 TID 的请求实际阻塞于 core dispatch；事件释放 callback 后，旧 Stop/Destroy 完成才发生后续 SetSurface。实际仅 2 代 decoder，中间 load 被覆盖，不能称三代均播放。seek=-12 是拒绝路径，日志时点与 playback_initialized=false 分支一致，不是 seek 成功。

真实 GPU 永久挂起、任意强并发/多实例、成功并发 seek、物理 HDR/主观声画、正式集成/候选替换仍待验收。formalArtifactAllowed=false。
