# Phase12 任务：历史 lexer 来源与实物门禁

输入：本目录 spec、plan、research、data-model、quickstart。只改 producer 新增诊断目录/专用 CI/文档；旧证据与消费端只读。按 TDD 执行。

## Phase 1：准备

- [x] T001 核验 Phase11 24224 项、TV 和业务基线，记录 out/phase12/precheck.json 与 solution-review-boundary.json。（FR12-01）
- [x] T002 保存方案快照到 out/phase12/planning-snapshot/archive-map.json，核实授权时间，保持 feature 指针和业务 index。（FR12-01/02）

## Phase 2：实施前门槛

- [x] T003 执行官方 prerequisite 并对 spec/plan/tasks 作只读语义分析，结果纳入 out/phase12/analyze-prerequisites.json 和实施报告。（FR12-01/07）

## Phase 3：US1 来源识别（P1，MVP）

独立验收：相同版本号/少数类型相同不判定身份；缺字段、原包/补丁/实际构建输入漂移拒绝。

- [x] T004 [US1] 在 tools/lexer-source-profile/tests/test_profile.py 写来源校验/历史、官方、Xcode 特征回归并保存 out/phase12/profile-red.log，覆盖注释伪阳性、冲突声明和短 revision。（FR12-03）
- [x] T005 [US1] 在 tools/lexer-source-profile/profile.py 最小实现严格文件 pin、来源与特征检测，保存 GREEN；记录仅证据自洽而非历史安装身份。（FR12-03/05）
- [x] T006 [P] [US1] 固定 upstream、Homebrew、Debian 的原始输入/完整 revision 与排除范围到 out/phase12/upstream-research；区分骨架静态排除与实测。（FR12-04）
- [x] T007 [P] [US1] 补查 Apple、Android/ANGLE 下游及预生成 skel.c，原始补丁和矩阵写 out/phase12/downstream-research，未知身份保留 unresolved。（FR12-04/05）

## Phase 4：US2 真实生成与对象门禁（P1）

独立验收：有效 pin 与命令记录下比较原始 stdout/Waf C/完整对象；特征吻合但 C 不同、C 相同但对象不同均不得通过。

- [x] T008 [US2] 扩展 tools/lexer-source-profile/tests/test_profile.py 覆盖输出/工具/M4/头文件/对象漂移、缺少编译输入、失败退出码、错误生成编码；先 RED。（FR12-03/05）
- [x] T009 [US2] 在 tools/lexer-source-profile/profile.py 实现生成/编译记录检查及精确匹配判断，GREEN 后用实际已固定证据核验。（FR12-05）
- [x] T010 [US2] 有可追溯候选时在 out/phase12/generation-controls 全新目录构建/生成；固定原归档/原补丁/实际编译骨架/M4/Waf/目标头文件；无新候选时重放一个既有固定工具作为门禁集成验证，不宣称新宿主构建。（FR12-05）

## Phase 5：US3 avformat 对齐或精确缺口（P2）

独立验收：源码输出相同才进入归档链接；没有匹配时提供具体输入/字段差异和来源缺口，绝不历史对象回填。

- [x] T011 [US3] 在 out/phase12/source-verification.json 汇总实际三方/新候选原始 C 与对象及 provenance gate；历史身份、source match 和 current Python 修复分别表示。（FR12-05/06）
- [x] T012 [US3] 若 T011 对象匹配，以源码对象进行 occurrence/顺序归档和 avformat map/GOT 对照；否则在 docs/producer-phase12-report.md 记录条件未满足的精确原因，不运行回填对照。（FR12-06）

## Phase 6：回归、CI 和交接

- [x] T013 在 .github/workflows/phase12-lexer-source.yml 添加限诊断分支/专用路径 CI，运行新门禁和相关原回归，下载日志/制品复验到 out/phase12；默认工作流不改。（FR12-07）
- [x] T014 完成本机新门禁与 Python 原回归，结果记录 out/phase12，运行入口说明更新 tools/lexer-source-profile/README.md 与本目录 quickstart.md。（FR12-02/07）
- [x] T015 复核旧封存/候选/默认/TV/业务 index、更新 tasks 与 docs/producer-phase12-report.md，封存 out/phase12/evidence-index.json、handoff.json。（FR12-01/07）

## 依赖与并行

T001→T002→T003。US1 的 T004→T005 为 MVP；T006/T007 只读研究可与测试开发并行。US2 T008→T009→T010，依赖 T005；US3 T011→T012 依赖 T010 和研究结论。T013/T014 在代码稳定后独立验证；T015 最后执行。测试必须先 RED 再实现，不能以来源下载失败作 TDD。

US1 并行示例：T006 upstream 与 T007 下游使用不同目录。US2 真实生成与来源只读检索可并行，不能与同一工具输入变更并行。US3 的 map 与完整 SHA 可并行读取同一已完成产物，归档/链接顺序执行。精确来源仍不可得时允许完成 US3 的明确缺口分支，但不得标记“来源已复现”。
