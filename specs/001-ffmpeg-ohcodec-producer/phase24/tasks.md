# Phase24 任务

## 初始化与基础
- [x] T001 复核冻结边界与授权，保存out/phase24/baseline-start.json及authorization.json（FR-001/009）。
- [x] T002 完成spec/plan/research/data-model/contracts/quickstart与官方脚本证据，目录specs/001-ffmpeg-ohcodec-producer/phase24（FR-010）。
- [x] T003 运行官方prerequisite并人工跨文档语义分析，保存out/phase24/spec-analysis.md。
- [x] T004 从out/phase23/app复制独立out/phase24/app，排除构建缓存和旧私有SMB夹具，校验七库相同（FR-001/008）。

## US1：指定NAS长播
- [x] T005 [US1] 在out/phase24/tests/test_contract.py先写短时间/EOF/缺失值/fallback/时钟/中断负例与正常窗口，观察RED（FR-003/004）。
- [x] T006 [US1] 在out/phase24/tests先写中文路径/编码URL/凭据错误日志脱敏RED（FR-002/005）。
- [x] T007 [US1] 实现out/phase24/tools/contract.py及app C++日志策略/低频采样/连续判定，运行GREEN（FR-003/004/005）。
- [x] T008 [US1] 实现out/phase24/tools/nas_preflight.py精确文件只读元数据预检和外部配置加载，不遍历目录（FR-002）。
- [x] T009 [US1] out/phase24/app接入独立短seek/恢复用例与3600秒真实播放场景，源码/HAP/maps绑定（FR-003/008）。
- [ ] T010 [US1] 用户凭据/设备就绪后执行指定文件预检、短测、连续长播，结果out/phase24/experiments（FR-002/003/004/009）。

## US2：HDR分层
- [x] T011 [P] [US2] out/phase24/tests/test_hdr_chart.py固定标准码值/边界/非8bit扩展的RED（FR-006）。
- [x] T012 [US2] out/phase24/tools/generate_hdr_chart.py实现并GREEN；编码三类样本，ffprobe/解码像素独立验证，out/phase24/fixtures/hdr（FR-006）。
- [x] T013 [US2] out/phase24/app接入三类×GL/VK×OHCodec/software、同实例HDR/SDR恢复与同transfer源切换；现有日志/属性/显示能力，禁止竞态getter（FR-007）。
- [x] T014 [US2] 指定电视执行矩阵并保存分层证据out/phase24/experiments，缺失值未测；稳定画面后才请求人工确认（FR-007/009）。

## US3：完整证据
- [x] T015 [US3] out/phase24/app执行devecocli构建、固化源码/HAP/七库绑定，保留实际失败（FR-008）。
- [ ] T016 [US3] 如库问题真机复现，先报告、独立来源RED/最小修复/双clean/新maps，out/phase24/experiments；无实际问题则不改七库（FR-008）。
- [ ] T017 [US3] out/phase24/ci隔离源码/规范/脱敏结果，运行测试/CI并复核制品，不含HAP/凭据/私人影片（FR-005/010）。
- [ ] T018 [US3] out/phase24/REPORT.md及manifest.json分项结论，最终边界复核、seal；人工/正式交付未通过保持pending（FR-001/009/010）。

依赖：T001→T002→T003→T004；T005/T006→T007→T008/T009→T010；T011→T012→T013→T014；T015在部署前，T016按实测需要，T017/T018最后。US1和US2主机测试可独立并行，真机只能主代理顺序操作，长播期间不部署。先完成日志和判定MVP，再短矩阵，再真实长播，最后复核封存。每个US均有独立接受标准见spec.md。

## 2026-10-20 阶段记录
T014表示19项场景执行并记录缺陷，不表示HDR完整通过：PQ硬解静态元数据缺失，默认GL为8bit，人工/系统回读未测。T010等待用户保存私有凭据，真实NAS预检/60分钟均未执行。T016仅完成源码定位与最小方案，本轮不扩大库重建。T018将建立可追加阶段快照，Phase24整体保持未完成。
