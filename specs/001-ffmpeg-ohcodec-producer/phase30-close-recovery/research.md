# 研究决策

## R1：失败范围限于旧实例

原版 `ohcodec_terminal_failure` 将 Stop/Destroy 的不确定结果传播到整个 PID，使不同视频和 Surface 也在平台 Create 前失败。选择按旧实例保守隔离；单独删布尔标志不足以避免两个生产者同时占用旧 Surface。

## R2：以 Destroy 结果决定释放

Stop 失败后仍执行 Destroy。Destroy 成功允许解除窗口引用和 Surface 预留；Destroy 失败不再次调用未知状态的旧平台句柄，保留稳定 callback userdata、锁和独立窗口引用。拒绝自动重试或立即释放：前者无法证明平台幂等，后者可能造成晚到回调悬空。

## R3：使用 Surface ID 而不是 wrapper 地址

同一 consumer 可产生不同 NativeWindow wrapper。注册表必须按 ID 判断冲突，在 SetSurface 前注册，并独立增加引用。mpv 的 NativeImage 仍属于消费方；不尝试代管其 GPU 状态。

## R4：验证层次分开

宿主测试覆盖竞态、旧回调、token、引用与平台调用序列；模拟器仅提供平台软件解码/缓冲交接证据。API 24 MatePad Air 两次分别注入 Stop/Destroy，证明同 PID 硬解与变化画面及设备音频输出。既有 Vulkan 注入无法替代这些错误。正常六库另有无注入真机回归。未验证 API 19 TV、挂起或耗尽。

## R5：复用已验收字节并绑定合并树

修复已形成正常 SDK 和三根重建一致性证据。此次补全流程不修改产品补丁与构建参数；合并后逐项绑定原 SDK 与源码。若产品文件在评审中变化，旧验收不能直接继承。PR 宿主 CI 本身不宣称重建 SDK 或真机验收。

## 已解决澄清

用户选择“本次交付到 FFmpeg SDK”，并追加要求完成 Spec Kit、提 PR、合并主分支后交付。实际主分支为 master。无需再决定消费者接入或修改用户原脏工作区。
