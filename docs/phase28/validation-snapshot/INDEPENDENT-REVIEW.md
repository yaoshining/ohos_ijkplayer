# Phase28 U1 复审通过（隔离诊断范围）

日期：2026-10-22。被审查 CI 提交：52572fe33511f306aef22dd489077446009ddad3。

结论：U1 可以关闭。在本轮检查范围内未发现新增阻塞项。此前 F1–F5、R1–R3 和本次 U1 的审查返修闭环完成；这不代表完整设备验收、产品恢复策略或正式交付获准。formalArtifactAllowed=false 保持。

## U1 核对

实际 generic mapper_uninit 在 UNSAFE 时同时标记 mapper/owner retained；实验宏下 abort，普通构建返回。外层 ra_hwdec_mapper_free 在 driver uninit 返回后再次检查 retained，跳过 talloc_free；ra_hwdec_uninit 在入口及回调返回后均检查 retained，防止继续 owner 析构/释放。SAFE 和 SAFE_RELEASE_ERROR 仍允许安全清理，后者保留 Surface terminal 状态以拒绝重建。

原有 unsafe-outer-free 使用真实外层 free、generic teardown 和 Vulkan drain，普通构建重跑通过。本次增加独立测试，继续抽取当前实际函数切片，平台操作仍为可控宿主 stub：

| 补充场景 | 结果 |
|---|---|
| SAFE 外层清理 | backend/owner uninit 各一次，mapper/owner 两次根释放，PASS |
| SAFE_RELEASE_ERROR 外层清理 | owner invalid，安全清理完成，PASS |
| owner 在自身 uninit 回调中设置 retained | 外层不释放，PASS |
| 实验宏下真实外层链发生 UNSAFE | 进程退出 -6（SIGABRT），PASS |

证据：[outer-free-regression.json](/private/tmp/phase28-review-5257/outer-free-regression.json)、[测试源码](/private/tmp/phase28-review-5257/outer-free-regression.c)。生产源码和原测试均未修改。

措辞精度：第一次进入 ra_hwdec_mapper_free 时，原有 unmap 仍发生在 driver uninit 前；后置检查阻止后续 free。对于入口已经 retained 的 mapper，则连 unmap/uninit 也跳过。不能把这两种情形统一描述为“首次 UNSAFE 前没有执行过 unmap”。此差异不改变本轮确认的外层释放修复结论。

## 验证结果

- 原测试独立重跑：mpv 10/10、ohdec 8/8 PASS；watchdog normal、experiment SIGABRT、missing-abort 变异拒绝、外部 hang timeout 全通过。结果：[mpv](/private/tmp/phase28-review-5257-mpv/results.json)、[ohdec](/private/tmp/phase28-review-5257-ohdec/results.json)、[watchdog](/private/tmp/phase28-review-5257-watchdog/results.json)。
- verify_handoff.py：PASS，53 项 seal、55 项 materials。文件字节绑定一致。
- GitHub 实时查询 [run 39657429022](https://github.com/yaoshining/ohos_ijkplayer/actions/runs/39657429022) success，head=52572fe33511f306aef22dd489077446009ddad3。artifact 12372108316 的远端 digest 与本地 artifact-04.zip 相同：3db70a414da7bd63d6efe35a98da96de8f933218f8e6d11b68e8a9c8fe11bd41。135 个文本文件、2,489,002 字节，全部索引匹配。见 [CI-live.json](/private/tmp/phase28-review-5257/CI-live.json)。
- 实读 a/b mpv：ef346b0c7c4c3a834501b419effbdb1523f5cdba05fda5fa0e282f693db59b88，两份一致。完整 FFmpeg 与 codec-only 仍分别为报告对应的 5e32a49d…/d90037f1…；本轮没有重做目标 clean 构建。
- HAP：1a79a08d10c932872cecfd3eef6e4b2d94acc2d03753ca2fbceab8dc1428cd41，内含 mpv/avcodec 与上述实际产物匹配；构建编译命令确认相关源文件启用了实验宏。
- 12 项受保护产物当前哈希匹配记录。上述产物校验详见 [evidence-audit.json](/private/tmp/phase28-review-5257/evidence-audit.json)。
- final-08 现有设备日志的 vk-pq/vk-switch/gl-pq/gl-pq-sw 结果与报告吻合，vk-switch loaded=4/eof=4/errors=0。展示 Surface 顺序切换与同 consumer 交接的声明界线仍保持。本轮未连接设备，日志核对不是新一次真机验证。

## 验收边界

普通构建 retained 是异常情况下保留对象的策略，不是资源回收或产品级恢复；本轮验收仅覆盖所审查调用链和隔离实验构建。不要将保留标记理解为整个应用/GPU 上下文的完整恢复保证。

以下继续待验收：目标机 GPU/Release 故障注入；同一 consumer 的 owner/NativeImage/稳定 ID 交接与强并发；Start/Configure、fallback、seek/reinit 设备覆盖；物理 HDR 与主观声画。后续进入独立验收阶段，无需重开已关闭的审查项；只有出现新失败证据才启动对应返修。

本轮只写 /private/tmp 审查材料，未改实现、原证据、Player/TV、候选库/HAR 或默认 SDK；未操作真机、未推送。继续只用应用保屏、不改系统设置。审查通过不授权替换候选、推送新 SHA 或发布。
