# Phase11任务

## Setup / Foundational

- [x] T001 复核 out/phase11/precheck.json 的TV、19052项旧证据与业务index；建立previous-versions归档。（FR11-01）
- [x] T002 官方setup-plan/setup-tasks完成，spec/plan/research/data-model/quickstart先后时序保留；只读analyze。（FR11-01/07）

## US1/US2：跨目录稳定实际参数

- [ ] T003 在 tools/ffmpeg8/tests/test_cross_root_inputs.py 编写真正失败的shell/clang/pkg-config测试，覆盖不同长度/空格、错误/缺失/预占入口。（FR11-03/04）
- [ ] T004 在 tools/ffmpeg8/build-env.sh、build-ohcodec.sh、producer-sdk.py 最小修复独立相对入口与真实绑定证据，GREEN。（FR11-02/04）
- [ ] T005 执行真实FFmpeg configure/目标编译小范围对照，确认参数和输入真实一致；保留out/phase11路径/对象证据。（FR11-03）
- [ ] T006 新增 tools/cross-root-profile/ 显式入口，拒绝paired不等；macOS两fresh全链并验证全SHA。（FR11-05）
- [ ] T007 新增专用phase11 CI工作流、实际Linux两fresh，下载实物与来源/工具/能力/八库/六库完整复验。（FR11-05/06）

## US3：精确源码对齐条件

- [ ] T008 [P] 在 out/phase11/source-research/ 解析当前TV与runtime对象命名指针，确认历史Python/运行目录冲突并先报告。（FR11-07）
- [ ] T009 [P] 在 out/phase11/source-research/ 逐项将可行历史控制转为固定源码单对象构建，绑定原始SHA及输入/命令；未闭环项具体列明。（FR11-07）

## Polish

- [ ] T010 复核既有归档映射与TV/业务边界，更新 docs/producer-phase11-report.md 与独立handoff/index，不改变候选/设备状态。（FR11-01/06/07）

依赖：T001→T002→T003→T004→T005→T006→T007→T010。T008/T009按计划研究步骤独立只读并行于路径修复，均先于T010。MVP为跨目录原始六库可重复；不存在新外部接口，contracts目录不适用。每项验收见spec，格式均为ID/任务/路径；解析器故障注入与sanitizer暂停，未列入本轮任务。
