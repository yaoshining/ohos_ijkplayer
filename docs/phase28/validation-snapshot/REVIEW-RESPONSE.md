# Phase28 独立审查返修记录

日期：2026-10-22。针对 `/private/tmp/phase28-review-extra-20261022/REVIEW.md` 的 F1–F5；`formalArtifactAllowed=false` 保持。

## F1 [P1] SAFE_RELEASE_ERROR 禁止重启问题 Surface

- 实现：`ohcodec_priv.surface_invalid` 作为 owner/Surface 生命周期状态；新增内部 `VOCTRL_OHCODEC_SURFACE` 查询/标记；`vo_gpu_next` 在 drain 返回 `SAFE_RELEASE_ERROR` 时立即标记；`vd_lavc` 在 `init_avctx` 入口调用 `ohcodec_lifecycle_refuse_init`，同一/下一 decoder filter 查询到 terminal Surface 时拒绝创建；`force_fallback`、`reinit`、`receive_frame` 的回退循环均检查 `lifecycle_failed`，不再无限重试。
- 测试：`tests/lifecycle/green-t005-19` 的 `surface-invalid-reinit`（真实 `reset_avctx` + `ohcodec_lifecycle_refuse_init`，同 VO 新 ctx 亦被拒绝）；baseline `red-t005-11` 该 case 语义失败。
- 残余：未在目标设备制造真实 `SAFE_RELEASE_ERROR`；状态机路径已覆盖。

## F2 [P1] Destroy 失败有界终局

- 实现：`ohdec.c` 新增进程级 `ohcodec_terminal_failure`；Stop 或 Destroy 失败即置位，后续 `oh_decode_create` 在创建平台 decoder 前返回 `AVERROR_EXTERNAL`，不再累积新 decoder。Destroy 失败保留 `ref->dec` 和泄漏的稳定引用壳（native handle 可追溯），日志携带失败计数；Close 仍返回 FFmpeg 忽略的 0。
- 测试：`tests/lifecycle/green-t008-11` 的 `destroy-fail`、`stop-fail`：首次 Close 只 Destroy 一次/Stop+Destroy 各一次，随后新 `oh_decode_create` 被拒绝且无新 `create` 事件；baseline `red-t008-09` 两个 case 均失败（会再次成功创建）。
- 残余：不把持续泄漏称为恢复方案；目标机平台 Destroy 错误注入未做。

## F3 [P2] empty-current 历史 external release

- 实现：`vk_mapper.external_release_inflight` 在 `signal_release` 成功后置位；drain 在 `current == NULL` 但历史 release 在途时，先在同一 graphics queue 上 `vkQueueWaitIdle`，再销毁 import；正常替帧路径不增加等待。
- 测试：`green-t005-19` 的 `empty-current-drain`：先真实 `mapper_release` 清 current，再真实 `ohcodec_drain`，断言 wait 早于 import destroy 且 result=SAFE；baseline `red-t005-11` 无 wait 即销毁，语义失败。

## F4 [P2] watchdog 门禁

- `run_watchdog.py`：仅接受 experiment 进程被 SIGABRT（-6/134）且无 `FAIL` 输出；timeout 不再是成功；修复 `TimeoutExpired` 返回四元组；新增 missing-abort 变异测试，要求门禁拒绝“返回 1 + FAIL”的变异体。
- 证据：`tests/lifecycle/t011-watchdog-06`：normal PASS、experiment -6、mutant 1 且门禁拒绝、watchdog-hang timeout 124。

## F5 [P2] 交接一致性

- 本文件、`REPORT.md`、`CURRENT.md`、`VERIFICATION.json`、`seal.json`、`IMPLEMENTATION-HANDOFF.json` 统一到返修后的状态；`verify_handoff.py` 独立校验 seal/handoff/关键入口哈希，避免循环依赖（seal 不包含 handoff，handoff 引用 seal）。
- 旧失败 CI `39635363231` 和旧审查记录保留；不把旧 `T005–T018 complete` 描述用于未返修提交。

## 验证与残余

- 新增/更新测试均以冻结 baseline 产生语义失败，再对 Phase28 源 GREEN。F1/F3/F2 的新增 case 是审查后补测，不以“源码修改前已写”表述；GREEN/RED 绑定真实函数切片。完整列表见 `tests/lifecycle/VERIFICATION.json`。
- 目标构建：完整 FFmpeg `libavcodec` a/b `5e32a49d...`；codec-only a/b `d90037f1...`；mpv a/b `b6e11499...`。
- 上一轮返修 CI（历史）：SHA `ba586a6096e4f8ae52a421832df5a515b3a77376`，run `39644855489` success，artifact `12365899306`。
- HAP：`5018c604...`，设备 Close/展示 Surface 顺序/GL/软件/keepScreen=false 复跑通过；同 OHCodec consumer 交接未验收（R3）。
- 未验收：目标设备 GPU wait 永不返回/SAFE_RELEASE_ERROR/UNSAFE 故障注入、强并发 producer 交错、物理 HDR/主观声画。
- 未验收：目标设备 GPU wait 永不返回/SAFE_RELEASE_ERROR/UNSAFE 故障注入、强并发 producer 交错、物理 HDR/主观声画。

## 复审 R1–R3 补充

- **R1**：通用 `mapper_uninit` 现在对 `SAFE_RELEASE_ERROR` 与 `UNSAFE` 都锁存 `owner.surface_invalid`；`mapper_init`/`mapper_map` 在 terminal 状态直接失败。新增 `mapper-teardown-release-error`：真实 generic teardown 让 Release stub 返回 `-123`，断言 owner 失效且新 mapper init 被拒。
- **R2**：新增 `ohcodec_hwdec_find/surface_invalid/mark_surface_invalid`，VOCTRL 在 mapper 缺失或属于其他后端时从 `hwdec_ctx.hwdecs` 持久 owner 查询，而不是只看 `p->hwdec_mapper`。新增 `surface-owner-invalid`：owner 有效、mapper 不存在时仍拒绝新 mapper。
- **R3**：报告已降级为“展示 Surface 不变、decoder 正常顺序切换”；final-07 旧/新 codec NativeWindow 分别为 `0x5b8b306fe0`/`0x5b8b306f40`，不再声称同一 OHCodec consumer 交接。同 owner/NativeImage/稳定 consumer Surface ID 的绑定列入待验收。

- 返修 CI：SHA `c5d9b26027100d3fa6880977d824ac917aa6012c`，run `39652500927` success，artifact `12370328139`，ZIP `a8db9ae6...`，131 文本文件全索引通过。
- HAP：`5018c604...`；mpv `b6e11499...`；FFmpeg `5e32a49d...`。

## U1 返修

- 外层 `ra_hwdec_mapper_free` 在调用 `driver->uninit` **之后**重新检查 `resource_retained`，UNSAFE 时跳过 `talloc_free`，不再无条件释放 mapper/import talloc 树。
- `ra_hwdec_uninit` 同样在 `driver->uninit` 之后检查 owner retained，跳过 owner free；普通构建保留策略与外层释放行为一致。
- generic `mapper_uninit` 在 UNSAFE 时设置 mapper/owner retained；`MP_OHCODEC_LIFECYCLE_EXPERIMENT` 下仍 abort（诊断 fail-stop），普通构建返回 retained。
- 新增 `unsafe-outer-free`：真实 `ra_hwdec_mapper_free` → generic uninit → Vulkan drain，queue wait 返回 -4；断言 mapper 指针被置 NULL、owner retained、backend/owner uninit 均未调用、进程未进入普通 free。baseline 该 case 语义失败。

- U1 返修 CI：SHA `52572fe33511f306aef22dd489077446009ddad3`，run `39657429022` success，artifact `12372108316`，ZIP `3db70a41...`，135 文本文件全索引通过；HAP `1a79a08d...`，mpv `ef346b0c...`。
