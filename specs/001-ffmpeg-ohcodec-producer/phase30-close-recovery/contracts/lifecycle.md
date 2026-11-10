# 关闭与恢复合同

| 状态/动作 | 平台资源 | 回调与 token | Surface |
| --- | --- | --- | --- |
| 创建 | 新句柄；SetSurface 前注册 | 新 ref/generation 与独立队列 | 独立引用；相同 ID 冲突返回 EBUSY |
| 开始关闭 | 等待已准入操作完成后 Stop/Destroy | detach、attached=NULL、generation 失效 | 仍由旧实例预留 |
| Stop 失败、Destroy 成功 | 句柄已销毁，不再调用 | 迟到 token render=ESTALE；discard 不 Free | 解除注册并归还独立引用 |
| Destroy 失败 | 句柄不可再用，保留到 PID 退出 | 壳/锁保留；四类旧回调不得访问已释放 context | 旧 ID 持续占用，新 ID 可创建 |
| 旧 token 最后释放 | 不重试 Destroy | 仅释放 token 引用，不跨 generation 操作 | 不释放隔离保留引用 |

FFmpeg 队列持有借用的平台指针/index，不把旧 index 交给新实例。正常同步对象随 context 回收；回调稳定壳独立存在。未更改公开导出 ABI。

正常 SDK 必须包含 libavcodec.so.62、libavformat.so.62、libavutil.so.60、libavfilter.so.11、libswresample.so.6、libswscale.so.9。buildOrigin=local，diagnosticInjection=false。故障库只能在独立测试输出下存在。
