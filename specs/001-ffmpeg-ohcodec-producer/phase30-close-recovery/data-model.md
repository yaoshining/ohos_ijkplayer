# 资源归属

OHCodecDecContext 属于单个 AVCodecContext。关闭后可清理其输入输出队列容器与同步对象。

OHCodecDecRef 是平台 callback userdata 和所有 AVOHCodecBuffer 的共同稳定对象，保存 gate、active、attached 和 generation。detach 后回调不能访问旧上下文。

Surface 注册表以 consumer Surface ID 为键。ref 持有 NativeWindow 独立引用，注册表由全局互斥锁保护。注册在 SetSurface 前完成，成功 Destroy 后解除。Destroy 返回错误时该实例继续占用原 ID，其他 ID 可独立注册。

输入/输出队列元素借用 OH_AVBuffer 指针和平台 index。旧 token 使用旧 ref/generation，其 render 和 discard 都经过准入检查。失败关闭不会向新实例归还旧 index。
