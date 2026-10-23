# 实施计划

1. 校验两份封存、当前TV/Player产物边界、设备及来源。选定独立feature，NO_PERSIST不改变默认指针。
2. 先固定事件协议/解析门禁测试，旧normal缺观测为可复现证据RED，不虚称已有生命周期缺陷。真实FFmpeg函数回归与删除active等待/提前SetSurface变异必须被门禁拒绝。
3. 在新完整输入副本中增加独立MP_OHCODEC_HANDOFF_TRACE仪表：正常owner稳定ID、decoder实例/consumer/线程/事件；不得打开MP_OHCODEC_DIAGNOSTIC或EXPERIMENT。
4. 测试专用MP_OHCODEC_HANDOFF_TEST仅添加显式arm/snapshot/release hook。hook挂在真实admit成功之后与真实Close等待处，使用独立状态，不持有产品gate等待应用，也不替换产品拒绝机制。只暴露在测试libavcodec中的av_ohcodec_handoff_test_*，不作为正式ABI。
5. 独立app复用现有normal接管、保屏、严格清理门禁；新A/B场景按事件推进。保留force-window，禁止把既有consumer-challenge日志当并发证据。
6. 精确锁定SDK/静态依赖/Python修复，独立目标构建和HAP身份，检查宏与导出。设备先A；若身份不持久则报告后再决定。B只在A基础上执行，采集流式系统日志，失败保留。
7. 新文本CI重放包、clean精确提交及完整预览；用户批准新SHA前不得push/远端CI。所有新证据新目录持久化，不覆盖旧封存。
