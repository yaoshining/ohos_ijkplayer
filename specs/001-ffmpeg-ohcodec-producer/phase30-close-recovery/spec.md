# Phase30 A 关闭错误后的会话恢复

## 用户需求

分别注入 FFmpeg OHCodec 的 Stop 和 Destroy 错误，核对旧回调、token、buffer 和 Surface 的归属。安全保留无法确认销毁的旧资源后，用户更换视频和 Surface，须能在同一 PID 恢复硬解并有画面和声音。

2026-11-10 用户追加要求继续云调试，最终完整修复问题。此文记录本次正式构建交接前的要求。首轮候选补丁和宿主测试已在本文建立前完成，其时间顺序沿用实际记录。

## 验收要求

- 原版分别复现两种错误导致新建在平台调用前返回 AVERROR_EXTERNAL。
- 关闭先使 token generation 失效，detach 回调，等待 active 操作完成。
- 旧 token 的迟到 render 返回 ESTALE，discard 不操作任何新实例的 buffer。
- Destroy 成功时可释放旧生产者的占用，即使此前 Stop 失败。
- Destroy 失败时保留旧回调壳、锁、句柄及生产侧窗口引用。旧 Surface ID 持续被拒绝复用，新 Surface 的独立实例可以启动。
- 同一个 Surface 的不同 NativeWindow wrapper 仍视为同一消费者。
- Stop、Destroy 两轮真机分别记录同一 PID 的 A 和 B，B 的 Surface ID 不同，B 为硬解，具有变化的画面与音频输出。
- 正常构建入口自动应用修复，并产生可核对源码和库摘要的 SDK。诊断注入只存在于独立测试库。
- Player、TV 源仓职责维持生产者与消费者分工，交付包含修复源与生产库，不修改历史封存。

## 边界

验证针对返回错误，未要求解决平台调用永久不返回。无法确认销毁的资源保留到进程退出，平台资源耗尽仍可能使后续创建失败。候选不承诺无限次数的失败恢复。
