# 内部生命周期合同

本轮不新增公开 FFmpeg API。新增 mpv 内部 VOCTRL_OHCODEC_DRAIN 及状态结构，受 MP_OHCODEC_LIFECYCLE_EXPERIMENT 编译开关控制；通用未启用构建不获得默认 fail-stop。

## 成功序列

decoder 调用线程串行发起 preflight；无 callback/queue/VO 锁跨同步 dispatch。VO 单次 QUERY 匹配 device/backend，NOT_APPLICABLE 立即返回且无副作用。适用时移出 current/queued，解锁后释放；清 renderer/source queue，执行 mapper drain，记录 GPU/外部队列完成、Release 返回，再清 last_src/import。ack 返回后才 Flush 或 Stop/Destroy；下一 SetSurface 最后。

平台 NativeImage 操作仅在 VO 线程。普通替帧不新增等待；生命周期 drain 幂等，没有 current 也需处理历史外部 release。已 retire 帧不能凭 last_token 复用；generation 保持陈旧输出拒绝。

## 错误合同

SAFE：完整正常成功。SAFE_RELEASE_ERROR：GPU 完成已知，归还错误必须上报且结束播放，不复用 Surface，可执行安全清理。UNSAFE：完成未知，禁止普通 free/Stop/import destroy/fallback；独立实验 fail-stop/watchdog 终止，记录为失败。无界 quarantine 和无限重试均禁止。GPU wait 无内建超时，外部 watchdog 必须从诊断 UI/worker 之外停止应用；此策略不是产品恢复验收。

Close 返回错误不能取消 avcodec_free_context。不得新增隐式 callback 后依赖错误返回保护上下文。codec gate 的上下文 detach 与 platform Stop/Destroy 的成功封口分开；原始错误保留。调用者不能从平台 callback 或其自定义日志函数重入同一 AVCodecContext 的 free/flush；同一 ctx 的生命周期由调用线程串行，这是接口前提。

## direct 与对照

direct FFmpeg 使用方先完成自己提交的 GPU 操作并归还 consumer buffer，再 free codec；本轮 direct 实验验证这一正确序列，旧错序反例原样保留。GL 不使用 Vulkan drain，不因 NOT_APPLICABLE 清除最终画面。软件路径行为不变。

旧平台 Destroy 必须在 Close 返回前完成。仍存活 token 的 reference shell 与平台 decoder 分离；最后 token unref 不执行第二次 Destroy。admission 同时覆盖 token 的 native release/render，Close detach 后阻止新操作并等已有操作结束。所有错误场景不得把单个 Stop 成功当成整个 producer 已退出。
