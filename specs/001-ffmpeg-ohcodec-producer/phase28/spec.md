# Phase28：OHCodec / Vulkan 关闭前归还

日期：2026-10-21。授权及原始边界见 `out/phase28/authorization.json`、`CURRENT.md`。本轮是独立实验修复，不修改 Player、TV、候选、默认 SDK 或旧阶段封存。原分支和已有脏改动保持。服务拦截历史保留，不能当成测试失败或测试通过。

## 用户故事与独立验收

### US1（P1）：关闭与同 Surface 切换

当 Vulkan 仍持有旧解码器输出时，明确关闭、重开或切源必须先让旧 GPU 工作结束并归还缓冲区，然后停止旧解码器，最后才能创建同 Surface 的新 producer。独立验收使用真实 mapper/VO/decoder 调用路径的事件顺序和本轮真机日志；没有后续视频帧时也必须完成，不依赖下一帧替换旧引用。

### US2（P1）：回调与错误收尾

所有四类 callback 的上下文访问必须受生命周期控制，Close 等待已进入的 callback 退出，拒绝新 callback 接触已清理上下文。初始化失败、重复清理及平台同步 callback 不死锁。GPU 完成未知与已完成但归还失败必须区分，禁止把 close 返回错误当作能够阻止 FFmpeg free。

### US3（P2）：播放行为与验证证据

正常替帧仍使用异步 fence；EOF 保留最后画面，收到新包、seek 或 Close 时才执行所需 reset。GL、软件解码、HDR/Python 修复保持。受影响库两次 clean 构建、精确新 CI、诊断应用真机及封存分别提供证据，不继承旧绿灯。

## 功能要求

- FR28-01：写入只在 `out/phase28` 与本规格目录；开始及结束核验三仓、12 基线产物、候选/default 和 Phase27 snapshot02。发现差异先报告。
- FR28-02：正常顺序为旧帧停止进入 VO → GPU 与外部 release 完成 → consumer buffer 归还 → drain ack → 旧 Flush/Stop/Destroy → 新 SetSurface/Prepare/Start。不得仅延后 Stop 或依赖 NativeBuffer 内存引用数。
- FR28-03：一次同步 VO dispatch 内完成能力查询、清 current/queued、立即清 gpu-next queue、mapper drain。等待 GPU 及释放帧引用时不持 VO internal mutex、callback gate 或 Surface callback mutex。
- FR28-04：仅匹配的 OHCodec Vulkan device 执行 drain；GL/软件/其他 device 返回不适用且不修改帧队列。已 retire 的旧帧不得因重绘再进入 mapper。单活跃解码器/单 VO 是本轮契约。
- FR28-05：codec callback userdata 改由稳定生命周期对象承载；四入口统一 admission/end，内部错误及格式应用拆 helper；同步 output_frame 格式路径同时修改。Close detach 后等待 active=0；Stop/Destroy 不持 gate/queue 锁。
- FR28-06：保留 generation 和 one-shot token 语义；覆盖初始化各阶段失败、Flush 暂停/恢复 admission、Close/重复 cleanup。平台成功 Stop/Destroy 的 callback 封口依据固定官方文档，错误返回不自动当成功。
- FR28-07：审计 reset_avctx、flush_all、uninit_avctx、fallback/reinit、prepare_decoding、EOF、新包、H264 first_packet bootstrap、filter reset/destroy。普通 EOF 的 reset 延迟至真正新包或显式生命周期边界，重复 NULL EOF 不重复 Flush。
- FR28-08：结果区分 SAFE、SAFE_RELEASE_ERROR、UNSAFE。SAFE 才正常继续；已完成 GPU 但归还失败须报告失败并结束播放，不复用问题 Surface；完成未知不得普通 free/fallback 或无界积累 decoder。本轮独立实验采用显式 fail-stop/watchdog 终局，不作为产品默认恢复方案。
- FR28-09：不新增公开 FFmpeg ABI，不改变原五库与 libplacebo 的部署字节；修复库范围为 libavcodec 和 libmpv。direct FFmpeg 用户负责先归还自身 consumer buffer，再调用 free；本轮不得宣称任意错序 direct 客户端自动安全。
- FR28-10：真实函数 RED 先于对应实现；保存源码切片/依赖/命令/状态/日志。覆盖关闭、EOF、seek、同 Surface 切换、重复 cleanup、错误及线程交错，不以玩具状态机代替真实入口。
- FR28-11：两 clean 根原始 SHA/ELF/真实输入核对，保留 HDR/Python 回归；重新生成本轮脚本清单及 patch 长度，保留旧辅助元数据不一致。CI 新提交需精确 SHA 批准，不沿用 Phase27。
- FR28-12：新 HAP/源码/库/maps 绑定后才计真机结果，只应用保屏；结束保屏 false、计划空、进程停止。主观声画、物理 HDR、任意 GPU 故障恢复未验证项保持 pending，formalArtifactAllowed=false。

## 成功标准

SC1：真实函数和设备时序均显示归还完成先于旧 Stop，下一 decoder 在旧 Stop 后才接入同 Surface；release 错误未被隐藏。

SC2：正常路径没有每帧全局等待，Close/seek 无依赖新帧的循环等待；所有回调收尾及初始化/错误用例给出实际结果。

SC3：两个独立构建相同，精确新 CI 与本轮设备证据可复核，受保护基线完全不变。任何未完成门禁不能升级为产品可发布。
