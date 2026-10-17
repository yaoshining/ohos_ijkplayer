# 任务与实际执行记录

- [x] T001 只读核实分支、改动、TV/HAR/mpv/六库及缓存静态输入。
- [x] T002 运行原 tests/test-sdk-contract.sh：通过（新增实现前）。
- [x] T003 建立 spec → plan/research/data-model/contracts → 本 tasks；仓库没有 Spec Kit 配置，未伪称调用 slash command。
- [x] T004 [US1/US3] 先编写 test_producer_sdk.py，运行记录 RED。
- [x] T005 [US1/US3] 实现可信基线导入、摘要核验、独立状态与 handoff。
- [x] T006 [US2] 迁移锁定 OHCodec 构建，校验源码/补丁/工具/静态依赖并输出 SDK。
- [x] T007 [US1/US2/US3] 运行 GREEN 回归、真实构建、ELF 门禁与逐库比较。
- [x] T008 更新中文操作说明、结果、缺口与消费路径。

依赖顺序按 T001–T008；不发布、不推送、不部署。真机验收为 pending，完整 SMB/TLS 依赖源码重建留作后续任务，不计为本次已完成。

## 最终状态（2026-10-17）

22 项回归通过；三补丁应用与反向 dry-run、真实 configure/make/install、打包恢复、ELF/导出/静态闭包门禁、SDK 重定位后的 ARM64 编译链接通过。源码六库 SHA256 全部不同，保留 imported-baseline。两次门禁 RED 和首次打包误报的真实经过见 docs/vidall-tv-baseline-producer-report.md。T007 完成的是构建与比较，不是字节一致性或设备验收。

未完成但不伪标通过：全部 SMB/TLS 依赖源码重建、历史工具链字节身份、重建六库字节一致、Player/HAR 集成验证、真机验收。所有设备状态 pending。Player/TV 全目录没有发生本会话写入。

## 第二阶段（追加授权，真实时序）

- [x] T101 重新核验 TV HEAD/HAR/libmpv/六库，全部一致。
- [x] T102 历史 prefix 独立实验：仅 swscale 恢复相同；定位 FFmpeg 误取父仓 revision=1bb2a7c3，原基线为 8.0。
- [x] T103 先失败回归，再实现版本隔离和稳定 prefix/DESTDIR。
- [x] T104 两次 clean 构建逐字节比较；单独核验历史基线复现。
- [x] T105 本仓隔离安装官方 Spec Kit v1.2.1，初始化宪章与 feature 并执行官方流程检查。
- [x] T106 下载 SHA 拒绝回归、统一来源锁；缓存历史证据与新源码选择分开。
- [x] T107 实际推进八静态库重建，记录每库结果和缺口。
- [x] T108 CI 接入 OHCodec producer、输入/审计/重复性门禁；缺闭包拒绝正式 SDK。
- [x] T109 更新 handoff、报告、分析与所有验证状态。

## 第二阶段结项状态

历史六库全字节复现、历史缓存依赖下两 clean、新源码八库依赖下两 clean 均通过；八库全部完成新源码重建。52 项回归通过，失败先行日志已保留。Spec Kit 官方 v1.2.1 初始化与真实流程前置检查完成。CI 专用入口、输入/审计/重复性/正式门禁实现完成，本机正式 gate 按预期拒绝；云端运行未执行，不能标为云端通过。

T109 最终报告：docs/producer-reproducibility-report.md。TV HEAD 观察变动但所有媒体字节相同，旧锁/包不变，handoff 分开记录。新导入包仅修正开发头文件，源自旧固定快照。源依赖 fullyVerified=false、设备 pending、宿主镜像/历史闭包/Linux CI 等缺口仍明确保留。

## 第三阶段（进行中）

- [x] T201 核验当前基线、远端权限与 runner；重新执行 Spec Kit 前置检查。
- [x] T202 工具漂移/缺失、库集合、头文件篡改、共享产物回归 RED→GREEN。
- [x] T203 八库两次独立 clean、比较 archive/对象/生成代码；前两组 RED，第三组 111/111 项一致。
- [ ] T204 构建前工具输入锁、固定 Linux 获取来源及漂移门禁。
- [ ] T205 专用最小提交/分支，实际远程 CI，保存 job 和 artifact 结果。
- [ ] T206 证据验证正反回归、状态分离、handoff 与最终报告。
