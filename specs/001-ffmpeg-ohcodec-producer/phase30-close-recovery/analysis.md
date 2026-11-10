# 规格一致性与实现收敛记录

日期：2026-11-10。基线为 master `33165069ce02718b63689e7c1f4a4256dcba31ae`，本次修复从 f23b708 单独移植。原型代码和真机验证先于此次文档补全；本记录不追认自动 workflow engine gate，也不把 prerequisite 当作语义评审。

## 流程执行

1. 阅读现有 spec/plan/tasks、宪章和实际 patch、build.py、test_recovery.py、recovery-case.c 及基线关闭流程。
2. 补全 US1–US3、FR-001–FR-010、SC-001–SC-004，research、contracts、quickstart 和需求质量清单。
3. 实际调用固定 v1.2.1 `setup-tasks.sh --json`，读取模板后生成 T001–T014 的依赖与证据映射。历史任务不伪造 RED/GREEN 先后。
4. 在最新 master 的隔离副本执行 `check-prerequisites.sh --json --require-spec --require-tasks --include-tasks`；显式选择本 feature，返回 research/data-model/contracts/quickstart/tasks。
5. 语义 analyze 按重复、歧义、未指定行为、宪章、覆盖与一致性六类检查；结果如下。该步骤只读，随后将结果归档为本记录。
6. implement/check：需求质量清单 8/8；新增 CI 执行同一回归；最新 master + 修复上再次跑原版和候选各 8 项 ASan/UBSan。32 个修复文件与原 f23b708 一致；没有产品代码变更，因此既有正常 SDK 来源未漂移。
7. converge：逐项核对实现和上述测试，未发现新的代码缺项，未追加空 Convergence 阶段。T013/T014 是已有发布执行门，须由实际 PR、merge 和最终绑定记录关闭，不能提前打勾。

无 `.specify/extensions.yml`，没有注册前后钩子。使用主分支既有脚本/模板，未升级全局 CLI。完整自动 workflow engine 没有运行，不宣称它的人工 gate 被系统批准。

## 覆盖映射

| 需求 | 任务 | 直接依据 |
| --- | --- | --- |
| FR-001 | T003、T004 | 原版 Create=1，候选 Create=2；移除进程拒绝 |
| FR-002 | T007、T008 | active drain、attached=NULL、generation 和四类旧回调断言 |
| FR-003 | T007、T008 | 迟到 render=ESTALE；discard 后平台 render/free 未增加 |
| FR-004 | T004、T007 | Stop 失败 Destroy 成功，原 ID 可复用；Destroy 仅一次 |
| FR-005 | T007 | 保留 quarantine_ref、窗口引用、ID；最后旧 token 释放后 callback 安全 |
| FR-006 | T007 | Surface ID 别名在 SetSurface 前拒绝；引用计数断言 |
| FR-007 | T005、T006 | 两个独立注入包及 PID 59523/63191 真机日志/截图 |
| FR-008 | T001、T009、T014 | 9921 源、静态依赖锁、唯一 patch、217 文件 SDK 清单 |
| FR-009 | T001、T008、T014 | 独立输出、本地构建标识、消费者只读、明确设备局限 |
| FR-010 | T002、T011–T014 | 全套文档、固定 prerequisite、专用 CI、待执行 PR/合并门 |
| SC-001 | T003、T008、T012 | 原版/候选各八项真实函数宿主回归 |
| SC-002 | T006 | 硬解、不同 Surface、变化画面、非零输出幅度及列表日志 |
| SC-003 | T009、T010 | 三根六库一致、无注入真机 A/B 回归 |
| SC-004 | T013、T014 | 合并前必须完成 CI/评审，合并后绑定 SDK；本记录时待执行 |

需求覆盖 10/10；成功标准映射 4/4；未映射任务 0；未解决规格歧义 0；重复冲突 0；宪章冲突 0。以上不表示发布执行门已完成。

## 代码审阅要点与限制

独立 NativeWindow 引用避免依赖消费方 wrapper 生命周期；注册表访问受 mutex 保护。旧 callbacks 通过保留的 detached gate 返回，旧 context/队列可以回收。成功 Destroy 才解除 Surface 占用；失败保留，不重试。旧 token 的 generation 准入阻断跨实例 buffer 操作。

ASan/UBSan 不检查故意保留资源的泄漏；平台资源耗尽和 Stop/Destroy 永久不返回不在本次覆盖。真机为 API 24 平板，不证明 API 19 TV。SDK 来自本地已验收构建，PR Ubuntu CI 只证明宿主回归。PR 评审中新产生的阻塞项必须处理后再合并。
