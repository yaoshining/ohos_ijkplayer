# 任务与验收追踪

2026-11-10：补全编号、依赖和证据位置。T001–T010 整理先前已执行事实，不声称当时先写了本文件。原始代码与测试见 f23b708。旧任务中的模拟器、云会话释放、生命周期回归、三根重建和正常包均保留。

## Phase 1：上下文与来源

- [x] T001 固定 `tools/ffmpeg8/phase30-close-recovery/inputs.lock.json` 全量来源，记录原型先于文档的事实（FR-008、FR-009）。
- [x] T002 补全本目录 `spec.md`、`plan.md`、`research.md`、`data-model.md`、`contracts/lifecycle.md`、`quickstart.md`、`checklists/requirements.md`，固定 `.specify/` 版本与 feature（FR-010）。

## Phase 2：原版复现

- [x] T003 用 `tools/ffmpeg8/phase30-close-recovery/test_recovery.py` 与 `tests/baseline-ohdec.c` 分别复现原版 Stop/Destroy 阻断，Create=1（FR-001、SC-001）。

## Phase 3：US1 恢复新实例

独立验收：同 PID、不同 Surface，B 进入平台创建，有硬解音画。

- [x] T004 [US1] 在 `tools/ffmpeg8/phase30-close-recovery/recover.patch` 移除进程级拒绝，依据 Destroy 结果释放或隔离旧实例（FR-001、FR-004）。
- [x] T005 [US1] 用 `tools/ffmpeg8/phase30-close-recovery/build_probes.py`、`probe.h` 分别构建错误库，首个已启动实例 skipped=1，其余调用真实（FR-007）。
- [x] T006 [US1] 保存 `tools/ffmpeg8/phase30-close-recovery/evidence/stop-accepted.txt`、`destroy-accepted.txt`、`verified.json`，核对 PID 59523/63191 的硬解音画、Surface、列表；释放云会话（FR-007、SC-002）。

## Phase 4：US2 旧资源隔离

独立验收：释放旧 context 与最后 token 后晚到回调安全；旧 ID 别名拒绝，新 ID 可用。

- [x] T007 [US2] 在 `tools/ffmpeg8/phase30-close-recovery/recovery-case.c` 检查 callback detach/drain、generation、ESTALE、discard、引用与别名；`recover.patch` 保留失败壳和 Surface 到 PID 退出（FR-002、FR-003、FR-005、FR-006）。
- [x] T008 [US2] 执行 `tools/ffmpeg8/phase30-close-recovery/test_recovery.py` 原版/候选各八项 ASan/UBSan；`device-probe.c` 软件模拟器仅证明真实缓冲交接（SC-001、FR-009）。

## Phase 5：US3 正常 SDK 与流程

独立验收：来源固定，无注入，三根六库一致；合并后确认交付。

- [x] T009 [US3] 用 `tools/ffmpeg8/phase30-close-recovery/build.py` 生成六库、头、许可证及 217 文件清单，在 `evidence/rebuild.json` 记录三根一致（FR-008、SC-003）。
- [x] T010 [US3] 在 `tools/ffmpeg8/phase30-close-recovery/evidence/normal-accepted.txt`、`normal-hap-binding.json` 保存 PID 12571 无注入正常 SDK 音画回归（SC-003）。
- [x] T011 [US3] 增加 `.github/workflows/phase30-close-recovery.yml`，PR/master push 运行 prerequisite 与宿主回归，保存证据，不代替设备验证（FR-010）。
- [x] T012 [US3] 执行固定 prerequisite、宿主、语义 analyze 与代码 converge，在本目录 `analysis.md` 记录覆盖与真实顺序（FR-010、SC-001）。

## Phase 6：PR、合并与最终交付

- [ ] T013 推送隔离分支、创建面向 master 的 PR，检查完整 CI 与评审；在本目录 `release-status.md` 记录发布前状态，PR 页面记录实际检查（FR-010、SC-004）。
- [ ] T014 经 PR 合并后核对 master SHA 与产品文件，生成 `out/phase30-close-recovery/delivery/merged-source-binding.json`，绑定已验收 SDK 后交付（FR-008、FR-009、FR-010、SC-004）。

## 依赖与实施策略

T001 → T002 → T003 → T004/T007 → T005/T008 → T006 → T009/T010 为逻辑依赖，历史实际顺序不追认。当前新增工作依序 T011 → T012 → T013 → T014。US1 与 US2 均为 P1，不可仅删除全局标志就交付；US3 完成才交付。文档审阅与 CI 文件准备可独立进行，本轮不用并行代理，不并行修改同一文件。
