# Phase23 任务

## Setup
- [x] T001 核实人类授权并在本地保存授权依据。
- [x] T002 核验Phase22/03、三仓与候选边界，保存out/phase23/previous-seal-verification.json及boundary-verification.json。（FR-001）
- [x] T003 执行官方初始化并形成spec/plan/data-model/contracts/quickstart于specs/001-ffmpeg-ohcodec-producer/phase23。

## Foundational
- [x] T004 汇总两项源码研究于specs/001-ffmpeg-ohcodec-producer/phase23/research.md，完成只读语义分析与官方prerequisite。（FR-002）
- [x] T005 复制独立应用/工具至out/phase23/app及tools，绑定输入且不读keys内容。（FR-001、FR-006）
- [x] T006 在out/phase23/tools建立采样与脱敏日志回归，连接指定设备，仅操作诊断bundle。（FR-007）

## US1 SMB
- [x] T007 [US1] 在out/phase23/tools/smb_server.py增加无凭据的数字协议阶段观测，先测试并保存out/phase23/tests/smb-observation-red.log。（FR-002、FR-003）
- [x] T008 [US1] 运行旧库目标RED并定位失败阶段，保存out/phase23/device-smb-01.log。（SC-001）
- [x] T009 [US1] 在out/phase23/input-package/sources 或 ffmpeg-input/source或工具层实现已证实根因的最小补丁；保存补丁及正常/边界/错误回归。（FR-002、FR-003）
- [x] T010 [US1] 在out/phase23/build构建受影响链双clean、绑定实际库与目标maps。（FR-006）
- [x] T011 [US1] 真机验证正确/错误认证、8MiB、六段seek、不可达端口及显式断开后重新打开，保存out/phase23/experiments/smb-matrix-06 和 final-combination-10。（SC-001）

## US2 Vulkan资源生命周期
- [x] T012 [US2] 在out/phase23/app采集至少3轮热身+10轮观察，每轮before/playing/destroyed/settled；失败读取不记0，固定和新Surface均运行，保存out/phase23/experiments/gpu-baseline-03 和 new-surface-baseline-08。（FR-004、SC-002）
- [x] T013 [US2] 根据所有权源码与阶段观测定位根因，先回归RED再在out/phase23/input-package/sources 或 ffmpeg-input/source修最小释放/生命周期路径。（FR-002、FR-004）
- [x] T014 [US2] 独立双clean重建受影响mpv/依赖，并绑定out/phase23/build库与maps。（FR-006）
- [x] T015 [US2] 重复同样目标循环与无播放器对照，量化稳定期、延迟回收及未解释增长，保存out/phase23/experiments/release-fix-09 和 final-combination-10。（SC-002）

## US3 默认GL
- [x] T016 [US3] 在out/phase23/app运行新进程GL-first与同Surface VK→GL、GL→VK→GL对照，保存out/phase23/experiments/gl-config-04。（FR-005）
- [x] T017 [US3] 来源层格式/恢复契约先RED，再修改out/phase23/input-package/sources 或 ffmpeg-input/source的窗口实际所有者，保存补丁；应用不代设SET_FORMAT。（FR-002、FR-005）
- [x] T018 [US3] 真机默认GL H264硬/软解、失败恢复、销毁重建与显式RGBA8对照，保存out/phase23/experiments/final-combination-10、final-gl-recovery-11、final-gl-stop-12、final-surface-pixels-13。（SC-003）

## 跨项收尾
- [ ] T019 复核新来源/补丁/工具链、ABI/导出、库/源/设备绑定；在out/phase23/ci准备可审阅提交并按新授权边界处理CI和下载复验。（FR-006、FR-008）
- [ ] T020 停止独立诊断和临时服务，复核旧封存/三仓/候选边界，在out/phase23/manifest.json和seal.json逐项记录通过/失败/未测。（FR-001、FR-007、SC-004）

依赖：T001–T006先行；US1和US2源码研究可并行，设备操作串行；US3复用US2资源观测但保留独立RED。每项测试先于对应修复。若受影响库无需重建，明确记录不适用和证据，不伪造双clean。最小可验收增量为US1完整读取/seek与认证，然后逐项收口；用户请求三项均持续推进。


进度证据补充：T008 实际 RED 为 device-smb-01.log；T010 不适用，根因是独立夹具最低方言，不改 SMB 库。T011 完整矩阵在 experiments/smb-matrix-06。T012 固定 03、新 Surface 08 均 13 轮；T013 07 跟踪及 tests/*-red/green.log；T014 最终 mpv/libplacebo 双目录字节一致见 build/final-dual-root.json，FFmpeg 双目录见 ffmpeg-input/dual-root-result.json。T016 03/04 有 fresh GL-first 和配置对照，T017 05 首次目标验证及 80 组函数回归。T015、T018 最终组合10及恢复11/12、像素尺寸13均完成。


- [x] T021 补齐GL硬/软解真实主动停止（12），与Vulkan停止→GL恢复（11）分别验收。
- [x] T022 修正探针vp/px接线，SurfaceSize真实函数边界回归与13目标八场景；16次NativeWindow geometry均匹配实际2880×1620像素，截图复核同布局。

提交前状态：T019的本地主机/来源/ABI/双clean/目标部分已通过，CI及下载复验以本次提交的工作流结果与执行制品为准，不预签通过。T020的诊断应用、服务及日志流已停止，旧边界复验通过；最终封存收据在本地out/phase23。
