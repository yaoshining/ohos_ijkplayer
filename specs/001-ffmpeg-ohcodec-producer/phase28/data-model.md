# Phase28 生命周期数据模型

## Decoder callback gate

归属 OHCodecDecRef，字段包括 codec、generation、attached AVCodecContext、gate mutex/condition、active count、admission 状态、初始化阶段、platform started/stopped 状态。状态：初始化 → attached → 暂停（Flush）→ attached，或 attached → detached → stopped → native_destroyed → shell_released。Close 内完成平台 Destroy，最后 token 释放仅销毁引用壳；旧 token 不得在新 producer 已启动时再次调用平台析构。四入口只在 admission 成功后访问 ctx，所有出口减少 active。detach 不持 input/output 锁等待；平台调用在锁外。成功 Destroy 后才释放 userdata；错误不得冒充封口。

## Surface drain 请求

字段：device_identity（调用者持有的 AVHWDeviceContext data）、reason（seek/close/reinit/resume）、phase（query/execute）、result、platform_error、实验事件序号。一次同步 dispatch 完成两 phase，不允许 query/execute 中间被 render 插入。

结果：NOT_APPLICABLE 无副作用；SAFE 已完成GPU和归还；SAFE_RELEASE_ERROR 已完成GPU但归还错误；UNSAFE 完成未知。只有前两种允许正常继续；后两者必须保留失败原因，不能重启问题 producer。

## VO / mapper 所有权

VO current_frame、frame_queued、gpu-next source queue 和 mapper last_src 是独立引用。锁内只转移指针，锁外释放；清 source queue 不等于清 last_src。Vulkan current import、window buffer、fence FD 和 cached imports 独立登记；系统接收 fence 后不由调用者再次 close。CPU 引用数不能证明 GPU 完成。

## EOF deferred reset

每个 decoder 的布尔状态，普通最终 EOF 置位，首个非空新包或显式 seek/close 消费。重复 EOF 不重复 Flush。reset 完成后清状态；失败不得假装已恢复。

## 验证身份

源码 baseline/delta、工具及资源、编译输入、库、HAP/maps、实验 session 和设备绑定分别记录。实验构建标记 MP_OHCODEC_LIFECYCLE_EXPERIMENT=1，产品发布 false；旧 Phase27 绿灯不可作为新身份验证。
