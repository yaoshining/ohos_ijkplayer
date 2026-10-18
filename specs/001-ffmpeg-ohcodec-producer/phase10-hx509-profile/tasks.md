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
- [x] T013 [US4] 汇总已解释、剩余缺证和最小方案到 docs/producer-phase10-report.md。（FR10-06、08）

## Polish

- [ ] T014 冻结复核、任务状态、独立handoff与证据索引 out/phase10/。（FR10-01、07、08）

依赖：T001→T002→T003→T004→T005→T006→T007；T008/T009在配方验证后执行；T010可在T004后先行，T011依赖对应平台生成输出；T012依赖新六库，最终T013→T014。US1为MVP。独立a/b根可并行；US3与US2运行可并行；US4不同库只读分析可并行。无跨任务写同一构建树。

恢复范围说明：主会话报告上一轮被平台 possible cybersecurity risk 系统错误中断；按恢复指令暂停 T010/T011 的故障注入与 sanitizer 边界执行，保持未完成，不改写测试规避限制。普通配置/漂移门禁、clean 构建及静态归因继续。


## 平台再次中断后的交接（2026-10-18）

- T001–T005 已有初始实现/验证证据；最后提交946d3aea的15项普通回归通过，新增Linux兼容回归仍为RED，兼容函数未实现。
- T006：本机a/b生成器完成，静态依赖后台进行中；未达到完整静态clean验收。
- T007：本轮六库manifest尚不存在，未验收。
- T008：独立CI已实际运行，但Linux Flex因__dead2未定义失败；平台中断后不再重试修复。
- T009：仅下载核验失败CI证据，不是成功产物验收。
- T010/T011：平台限制下暂停，未完成，无行为通过声明。
- T012：旧map及归档顺序可行性证据完成；新产物控制链接尚未运行，仍未完成。
- T013：已保存阶段报告的真实未完成状态。
- T014：冻结边界复核与交接快照已保存；因后台日志可变，不提供最终封存索引或完成验收声明。

最后专用提交946d3aeabe6bcb29e0fc933ef4980f527e605b69；CI39108567338失败。本机后台根PID62999的只读快照见out/phase10/processes-at-handoff.json，不启动额外构建、不修改冻结recipe。后续需重新核实进程是否结束、日志与实际构建结果，不能继承进行中状态为通过。

## Resume-01（直接用户消息01a14e02-22c8-7691-a158-4f6f619efed0）

已核实本轮继续普通构建兼容与静态归因的授权。旧交接65项全部匹配，并复制到 out/phase10/resume-01/previous-snapshot，原索引与archive-map保留；本轮报告/索引另存，不将旧路径修改后的字节冒称旧版本。

- [ ] T015 Linux Flex兼容RED→最小实现→GREEN：仅Linux宿主声明/链接BSD库及禁用Darwin相邻M4查找；兼容头/补丁/实际libbsd及libmd预后锁定，生成骨架不变。
- [ ] T016 补充缺库失败和平台隔离回归；新CI实际两fresh与下载复验；默认工作流不变。
- [ ] T017 核实既有local-final后台退出、两依赖/两六库及固定root控制，区别宿主辅助liby.a和八目标库。
- [ ] T018 本轮新SDK exact relink及version/GnuTLS/runtime对象/保留occurrence的归档排序控制，产出独立resume报告/交接/索引。

只读analyze：新增事项映射FR10-01/03/05/07/08；Linux兼容仅诊断分支，Mac已执行路径不变；无CRITICAL。T010/T011仍暂停，不包含在本轮恢复范围。

- [ ] T019 M4 单变量原文/同 NDK 对象归因；为精确版本输出门禁写真实 RED，再最小实现、GREEN、真实 Waf/CI 验证。对应 FR10-03/04/05/07，原文差异分列，不放宽为通用归一化比较。

T019 只读一致性分析：与 US1 的原文验收范围已同步；默认路径、设备和暂停项边界不变，无 CRITICAL。
