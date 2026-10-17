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
- [x] T204 构建前工具输入锁、固定 Linux 获取来源及漂移门禁。
- [x] T205 专用最小提交/分支，实际远程 CI，保存 job 和 artifact 结果。
- [x] T206 证据验证正反回归、状态分离、handoff 与最终报告。


第三阶段最终状态（2026-10-18）：本机与Linux均完成八库111项和FFmpeg六库/开发文件的两次fresh字节一致。83项回归通过。最终CI 39046623487、提交004546a5两job成功，下载后ZIP外部摘要、SDK固定manifest和实物比较再次通过。新选Linux来源闭包true，历史身份false；formalArtifactAllowed=false，设备pending。原TV字节包和原工作树/分支保持。人工review gate仍未声称获批。

## 第四阶段（2026-10-18）

- [x] T301 fresh核验TV完整组合、读取Spec Kit工件及执行前置检查。
- [x] T302 ELF节/符号/对象审计工具先RED再GREEN。
- [x] T303 四组SDK与中间控制组分层比较，执行可隔离对照实验。
- [x] T304 只读历史记录/缓存源码/对象/配置绑定与API24证据调查。
- [x] T305 proven/inferred/missing矩阵、差异报告、handoff和规格分析更新。

第四阶段结项：93项回归通过；当前TV组合不变，独立重链接精确复现新macOS libavformat；2636历史归档成员绑定现存对象；当前Native官方签名/完整17415项与phase3预锁绑定完成。调查完成不等于缺证消失：历史执行身份仍false、GnuTLS探测缺陷仅隔离未修复、Linux/API24行为未等价、设备pending、正式发布false。报告docs/producer-phase4-investigation.md，未改recipe/锁/冻结包。

## 第五阶段（已完成诊断验证，2026-10-18）

- [x] T401 fresh核验TV组合、GMP差异，更新Spec Kit并执行前置检查。
- [x] T402 真实静态链/构建函数/能力核验RED→最小修复→GREEN。
- [x] T403 构建前冻结recipe与工具，本机两次全fresh八库、能力门禁与比较。
- [x] T404 两次fresh FFmpeg/OHCodec构建、SDK核验和比较。
- [x] T405 专用最小提交、真实CI、下载artifact独立复验。
- [x] T406 与TV和旧诊断差异、未解决项、报告/handoff及最终冻结边界审计。

第五阶段结项：102项本机/CI回归通过；macOS和Linux两clean均完成静态111项及FFmpeg六库/开发文件字节一致。GMP恢复历史archive，两个GnuTLS真实曲线表项恢复。CI39053017312/2837eab5 success，artifact外部SHA与下载实物、两个固定SDK及曲线门禁独立复验通过。未替换候选/基线，未修改来源锁；HAVE_ICONV/GnuTLS加速包装/Samba等差异与历史缺证仍保留，设备pending、正式false。

## 第六阶段（进行中）

- [x] T501 重新读取约束与Spec Kit，fresh核验TV组合。
- [x] T502 历史配置/探测/源码/实际对象逐项差异矩阵，报告最小方案与冲突。
- [ ] T503 GnuTLS真实失败测试、最小配置修复及能力门禁。
- [ ] T504 Samba真实失败测试、最小修复/独立诊断及路径门禁。
- [ ] T505 全新两clean八库及FFmpeg、实际能力与基线差异验证。
- [ ] T506 专用分支最小提交、真实CI与下载实物复验。
- [ ] T507 更新最终报告/handoff、边界审计与证据索引。
