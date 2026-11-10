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

## 技术与文件结构

- C / pthread / FFmpeg AVBufferRef；OpenHarmony arm64 平台接口。补丁、正常构建、诊断构建和宿主测试位于 `tools/ffmpeg8/phase30-close-recovery/`。
- `recover.patch` 是唯一产品代码变更；`tests/baseline-ohdec.c` 为固定原版源，`test_recovery.py` 抽取实际函数后以 clang + ASan/UBSan 执行。`recovery-case.c` 检查旧实例资源归属。
- `build.py` 输入校验、全量编译及清单归档；`build_probes.py` 和 `probe.h` 仅在独立副本构建返回错误注入库；不得混入正常 SDK。
- 主分支既有 `.specify/` 保存固定版本脚本、模板与宪章，本轮显式通过 SPECIFY_FEATURE_DIRECTORY 选择 feature；本 feature 包含 research、data-model、contracts、quickstart、checklists、tasks 和 analysis。
- 新增 `.github/workflows/phase30-close-recovery.yml` 在 PR 与 master push 执行同一宿主回归和 prerequisite；现有仓库门禁保持。

## 宪章检查与执行顺序

I：只修改 producer，消费者只读。II：保持历史封存和 TV 制品；本轮仅交付新 SDK。III：已存在原版复现与候选 GREEN，文档补全不追认先前未发生的流程。IV：保持完整来源清单、许可证与二进制摘要。V：仅引用本次 API 24 验收，不扩大到 TV 或资源耗尽。

用户追加流程要求后顺序为：核对原实现与证据 → 补全规格/研究/合同 → 生成有 ID 的任务 → analyze → 补齐 CI 和发布追踪 → implement/check → converge → PR/检查/评审 → 合并 master → 核对已验收 SDK 与合并源码绑定 → 交付。T001–T010 对既有事实追踪，后续任务记录本轮新增工作，禁止倒填未运行的检查。

交付复用已验收的正常 SDK，不重新编译来制造不同字节。最终核对合并树中的补丁、build.py、inputs.lock.json、许可证与已验收 SDK 对应来源；任何产品源差异要求重新评估构建和设备验收。
