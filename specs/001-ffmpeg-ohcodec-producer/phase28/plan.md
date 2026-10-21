# Phase28 实施计划

日期：2026-10-21。当前业务分支 `yaoshining-hdr-playback` 保持；所有实验在独立目录。输入 [spec.md](spec.md)。官方 setup-plan 已执行，记录 `out/phase28/setup-plan.json`；使用 SPECIFY_FEATURE_NO_PERSIST，不更改 feature 指针。此文档先于产品源实现。

## 技术与范围

C11 / pthread / FFmpeg OHCodec，mpv C / VO dispatch / libplacebo Vulkan，Python 3 标准库保存证据。目标 HarmonyOS ARM64，宿主 macOS 与 Linux CI 分开验收。以 Phase27 最终源码为唯一 baseline，改 libavcodec 与 libmpv，原五库和 libplacebo 固定。目录布局：out/phase28/{ffmpeg-input/source,input-package/sources/mpv,build-runtime,tests,build,ci,app,experiments,research}；全部新 run-root 必须不存在。

性能约束：正常替帧保持异步，不新增每帧 finish。生命周期等待只在 Close、seek、reinit、EOF 后真正新包。单活跃 decoder / 单 VO；不宣称任意第三方消费者或多路并发 Surface 已支持。

## 方案

1. mpv `vd_lavc` 在 void Flush/free 前调用可返回结果的 preflight。VO 一次同步 dispatch 内 QUERY 匹配 device/backend，然后锁内移出 current/queued、锁外释放，EXECUTE 立即清 gpu-next queue，再调用 OHCodec Vulkan drain。GL / 软件不适用且无状态变更。
2. drain 完成 libplacebo 工作与实际 graphics queue 的外部 release，当前 buffer 在 GPU 完成后归还，最后清 mapper last_src 和 import。处理 empty mapper 仍有历史外部 release 的情况。新 decoder 必须在旧 Close 完成之后初始化。
3. codec 使用 decoder-owned callback gate；detach/drain 后 Close 内 Stop 和 Destroy；仍被其他线程持有的旧 token 仅保留已失效的引用壳，不得延后平台 Destroy。不能把 Stop 推迟到新 decoder 已接入之后。成功平台调用按固定官方 callback 契约收尾，错误必须记录并走失败终局。
4. 普通 OHCodec EOF 设置 deferred reset，保留最终画面；新 packet/seek/Close 消费该状态，恰一次 reset。bootstrap first_packet 没有帧发布到 VO，可走已证明的无 mapper 分支，但仍进入统一调用清单。
5. GPU 已完成但 Release 错误：本轮标失败，结束播放并有界清理，禁复用问题 Surface。GPU 完成未知：禁止普通 FFmpeg free、平台 Stop、import 销毁或 fallback。独立诊断构建显式启用 `MP_OHCODEC_LIFECYCLE_EXPERIMENT=1`，将此终局交给实验 fail-stop/watchdog；通用 mpv 未启用该宏时不得获得默认 abort。实验策略写入构建锁、HAP binding 和 manifest，产品可恢复策略待单独设计。
6. watchdog 在诊断 worker 之外；vkQueueWaitIdle 没有 timeout，外部进程监视时间线超时后终止唯一诊断应用并收集日志。不能等待卡住的 UI/worker 自己执行停止。宿主故障用子进程 timeout；设备正常序列不人为破坏系统 GPU。

## 验证顺序

真实 Phase27 mapper_uninit/mapper_release、vd_lavc reset/uninit/EOF 和 oh_decode callbacks/close 作为 RED；平台 API 用可控 stub，真实函数及依赖摘要绑定。随后只改对应 Phase28 副本，再 GREEN；测试涵盖 contracts/lifecycle.md 中的所有状态和失败分支。每次等待用 barrier/condition 控制，不用随机 sleep 证明无死锁。

再跑 Phase27 HDR/SEI/AnnexB/优先级和 Python 污染门禁。两 clean FFmpeg/mpv 构建、原始 SHA/ELF/编译及链接输入核验；新独立 CI checkout、本地干净重放、精确 SHA 批准后推送，下载 artifact 全索引复核。最后新 HAP+maps、单次 Close、连续播放、EOF 恢复、seek、同 Surface 同参数切换、GL/软件对照；结束清理并封存。

## 宪章与门禁

三仓职责/只读边界及 Phase27 snapshot02 已核验；原钥匙和业务脏改动不触碰。TDD 未完成则不能宣布实现验收；新 CI 未批准则止于本地完整预览；未设备验证则 pending。根 .gitignore 已覆盖 out，独立文本 CI 使用白名单，不修改根 ignore。没有 extensions.yml，无前后 hook。

设计后审查：没有新增公开 FFmpeg ABI；mpv 内部实验开关明确，产品终局未解决并保留正式 false。这是显式实验边界，不伪称通用播放器恢复完成。当前设计可进入回归验证，关键实现风险由 T003/T006/T009 的真实函数与编译门禁约束。

## 复杂度与备选

拒绝仅搬 Stop（GPU fence 与同 Surface 不安全）、codec close callback 返回错误（FFmpeg 忽略）、每帧 QueueWaitIdle（不必要性能退化）、无界保留旧 decoder（资源不收敛）、复用延迟 VOCTRL_RESET（无新帧无法清理）。若真实入口证据推翻当前方案，先记录并更新规格，不能静默扩展固定库/公开 ABI。
