# Phase30 同 consumer 交接与真实线程交错

该目录是独立宿主 CI 重放材料，不是候选库或可发布应用。`formalArtifactAllowed=false`。

执行：`python3 -B tools/phase30-consumer-handoff/runner.py --out /绝对路径/checkout外的新目录`。默认拒绝脏 checkout；开发可用 `--allow-dirty`，其结果不作为精确提交证据。

覆盖 A/B 解析门禁各16项、真实 FFmpeg 回调/Close 8项、删除真实 Close active 等待的语义失败变异、实际 dispatch 两种等待与正常快路、测试钩子身份/状态、入口模式一致性、完成门禁、精确 PC 重定位门禁及 CI 上传/身份门禁。解析夹具不是设备运行；host 线程测试不是目标 GPU 故障注入。hook state=7 用直接设置验证终态不可倒退，不声称真实5秒超时。

本地 A02 和 B03 的有限真机结果见规格及 provenance 摘要。A 为 TRACE-only；B 为 TRACE+TEST，保留 normal 注册与 UNSAFE 接管策略，未启用旧 DIAGNOSTIC/EXPERIMENT。B 的两条命令请求通过真实 mpv core dispatch，测试钩子仅控制时间，不替代产品 gate。范围限单 mpv 实例，seek=-12 拒绝，不声称 seek 执行成功或所有 load 都播放。

`application/` 包含当前 B 应用完整自有文本与所用第三方头，A 的 expected.h 在 application-variants。原始冻结索引包含全部资源摘要；非文本资源另列，不上传媒体/字体/图像。目标 SDK、外部库和签名不在此包内，因此 CI 不构建 HAP；实际本地构建证据独立保留。

历史输入缺口：phase25_runner.inc、integration.c、preflight.c、play_policy.c 等不在上一阶段远端包或1365项封存。当前从本地恢复并在本轮冻结、重建、重新验证；不能追认上一阶段源码闭包。新 A/B 各224项快照、各734项编译器依赖均有本地逐字节核验。

保留所有已知失败：FFmpeg A syscall 声明、mpv FRAME 错位、PC收集器、TEST导出门禁、B入口空计划及 RTLD_DEFAULT 不可见。旧失败不改写为通过。提交只包含源码、规格、许可、宿主测试和脱敏摘要，不含原始设备 dump、签名/凭据、HAP/库/SDK。

真 GPU 永久挂起、任意强并发/多实例、物理 HDR/主观声画、正式应用接入继续待验收。推送需精确 SHA 批准。

application/BUILD-NOTES.md 为本轮新打包说明，原说明与新说明哈希转换见 provenance/packaging-transforms.json；冻结源码未修改。
