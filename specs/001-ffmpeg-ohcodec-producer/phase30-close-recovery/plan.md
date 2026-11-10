# 实施与验证计划

## 实现

移除进程级 Stop/Destroy 拒绝标志。以受互斥锁保护的 Surface ID 注册表记录每个生产者，SetSurface 前取得 NativeWindow 独立引用和注册占用。成功 Destroy 是释放边界。失败 Destroy 的 AVBufferRef 转入实例上的保留引用，旧 gate 保持 detached，原上下文和 FFmpeg 队列可以回收。

继续复用原有回调准入、active drain、generation 和 token 幂等释放流程。应用侧 NativeImage 归 mpv，FFmpeg 保留生产侧窗口，不接管 mpv GPU 对象。

## 来源与验证

从摘要固定的完整 Phase30 A 输入派生到全新目录，构建脚本自动应用唯一补丁并核对修改后的文件摘要。独立宿主测试固定原版函数及既有平台替身，原版复现阻断，候选验证恢复、旧回调、旧 token、同 Surface 别名拒绝和原有六项生命周期回归。使用 ASan/UBSan。

诊断库在首个已启动且已绑定 Surface 的实例上，分别跳过一次 Stop 或 Destroy 并返回 AV_ERR_UNKNOWN，另一项仍调用真实接口。这样 Destroy 注入保留真实平台实例。按应用日志、硬解属性、连续屏幕帧、音频幅度及进度推进联合判断。

正常 SDK 构建关闭所有注入和实验宏。独立两根重建比较运行库字节。清单明确本地构建来源及所用输入，作为生产者交接包。

## 一致性分析

新 Surface 可以恢复和旧 Surface 不得复用必须同时成立。仅删除全局布尔变量会缺少后一个约束。Stop 失败且 Destroy 成功时继续保留占用会误拒绝正常资源，必须依据 Destroy 的结果释放。已销毁实例的旧 token 仍持壳时，壳释放路径不能重复 Destroy。

原始云截图和日志存放在本地本轮目录，发布文档仅使用脱敏摘要。原型实现先于本次文档已明确标注。官方 prerequisite 检查已实际通过，语义一致性依据上述代码路径及断言逐项核对。
