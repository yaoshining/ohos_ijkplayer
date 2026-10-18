# Tasks: Phase10 HX509 独立历史诊断配置

输入：spec.md/plan.md；官方setup-tasks已选中本增量目录；无extension hooks。

## Setup

- [x] T001 复核TV、全部旧索引、业务/默认指针，写 out/phase10/precheck.json。（FR10-01）

## Foundational

- [x] T002 官方前置检查和只读analyze，保留 out/phase10/prerequisites.json；随后实施前检查。（FR10-04）

## US1（P1）：显式历史配置

独立验收：真实Waf输入选择和生成、默认/非HX509路径不变，漂移/错误失败关闭。

- [x] T003 [US1] 在 tools/hx509-history/tests/test_profile.py 写显式选择、非目标、输入/资源漂移和真实Waf生成RED。（FR10-02、03、04）
- [x] T004 [US1] 实现 tools/hx509-history/profile.py、waf_select.py、sources.lock.json，最小GREEN并保存 out/phase10/tdd/。（FR10-02、03、04）
- [x] T005 [US1] 实现 tools/hx509-history/run.py 冻结recipe副本和预锁，注册profile来源/工具/补丁证据且保留默认锁。（FR10-01、03）

## US2（P1）：跨平台两fresh

独立验收：每次重新构建生成器、八依赖、FFmpeg，逐层报告，无复用对象冒充clean。

- [ ] T006 [US2] 执行macOS两fresh生成器/静态依赖，产物 out/phase10/local/ 与比较清单。（FR10-03、05）
- [ ] T007 [US2] 用对应静态输入执行macOS两fresh六库，必要时另作固定root对照，记录 out/phase10/local/。（FR10-05、08）
- [ ] T008 [US2] 新增 tools/hx509-history/ci.sh 与独立opt-in workflow入口，测试默认路径不变；专用分支实际Linux两fresh构建。（FR10-05、07）
- [ ] T009 [US2] 下载并独立核验Linux实际artifact，生成 out/phase10/ci-verification.json，分别报告NDK/宿主差异。（FR10-03、05、07）

## US3（P1）：真实边界执行

独立验收：同源码的历史/当前生成器对照，逐例进程结果与sanitizer，不把捕获故障算功能通过。

- [ ] T010 [US3] 在 tools/hx509-history/boundary/ 编写真实parser/lexer harness和用例运行器，含正常/空/非法、长token/引号/EOF、增长/溢出、分配失败。（FR10-04、06）
- [ ] T011 [US3] 两平台实际执行ASan/UBSan矩阵，保存 out/phase10/*/boundary/；故障立即报告并保留负面证据。（FR10-06）

## US4（P2）：剩余完整哈希

独立验收：新产物控制先全SHA复现，再区分新源变化与历史置换归因。

- [ ] T012 [US4] 新输出的version/GnuTLS/Samba分层控制与对象/字符串/map分析，写 out/phase10/hash-investigation/。（FR10-08）
- [ ] T013 [US4] 汇总已解释、剩余缺证和最小方案到 docs/producer-phase10-report.md。（FR10-06、08）

## Polish

- [ ] T014 冻结复核、任务状态、独立handoff与证据索引 out/phase10/。（FR10-01、07、08）

依赖：T001→T002→T003→T004→T005→T006→T007；T008/T009在配方验证后执行；T010可在T004后先行，T011依赖对应平台生成输出；T012依赖新六库，最终T013→T014。US1为MVP。独立a/b根可并行；US3与US2运行可并行；US4不同库只读分析可并行。无跨任务写同一构建树。

恢复范围说明：主会话报告上一轮被平台 possible cybersecurity risk 系统错误中断；按恢复指令暂停 T010/T011 的故障注入与 sanitizer 边界执行，保持未完成，不改写测试规避限制。普通配置/漂移门禁、clean 构建及静态归因继续。
