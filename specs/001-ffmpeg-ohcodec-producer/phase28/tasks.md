# Phase28 任务清单

## Setup 与基础

- [x] T001 核验授权、三仓/12产物、Phase27 snapshot02，保存 out/phase28/authorization.json、boundary-verification.json、phase27-precheck.json。（FR28-01）
- [x] T002 整合三份 research、官方 callback 文档、当前 Spec Kit 设计与 contracts，保留 out/phase28/service-block-investigation.md。（FR28-02..09）
- [x] T003 对 spec/plan/contracts/tasks 执行官方 prerequisite 与语义一致性分析，保存 out/phase28/analysis.json；明确实验宏和不可恢复错误边界。（全要求）
- [x] T004 复制最终 Phase27 源与脚本至 out/phase28/{ffmpeg-input,input-package,build-runtime}，生成 baseline 精确集合锁，禁止复用旧 build。（FR28-01、11）

## US1：归还与 producer 顺序（P1）

- [x] T005 [US1] 在 out/phase28/tests/lifecycle/ 提取真实 mapper_uninit/release、vd_lavc reset/uninit、VO control 建立顺序 RED，保存编译成功与语义失败。证据：tests/lifecycle/red-t005-08、RED-BASELINE.json。（FR28-02、03、10）
- [x] T006 [US1] 在 Phase28 mpv 副本实现内部 preflight、同步 VO 清理、Vulkan drain、展示 Surface 不变时旧 Stop/Destroy 先于新 SetSurface；同一 OHCodec consumer 交接仍待绑定验收，正常替帧无全局等待。实现：vd_lavc preflight/EOF延后、vo.c retire、vo_gpu_next capability-gated drain、ohcodec_interop drain；GREEN 见 tests/lifecycle/green-t005-12。（FR28-02、03、04）
- [x] T007 [US1] GREEN：无新帧、相同参数复用、旧帧重绘、旧token晚释放、重复drain、异步外部队列与错误返回；所有实际函数依赖绑定。green-t005-26 覆盖同步 drain/历史 external release/旧 token、mapper teardown release-error、owner 查询；设备 vk-switch 覆盖展示 Surface 顺序，未证明同一 consumer 交接；日志标签瑕疵保留说明。（FR28-02、04、08、10）

## US2：callback 与错误收尾（P1）

- [x] T008 [US2] 在 out/phase28/tests/lifecycle/ 建立真实 ohdec 四callback/Close/Flush/token/native-op 的 RED，覆盖在途与同步callback及ctx释放后的晚到调用。证据：tests/lifecycle/red-t008-07、RED-BASELINE.json。（FR28-05、06、10）
- [x] T009 [US2] 在 Phase28 ohdec 副本实现稳定gate、detach/drain、内部helper、token admission，Close内Stop/Destroy、旧token仅留失效壳。GREEN 见 tests/lifecycle/green-t008-08。（FR28-05、06）
- [~] T010 [US2] GREEN：各初始化失败、重复清理、generation、格式fallback、锁顺序，平台错误失败终局；不以close返回值取消FFmpeg free。已覆盖 Prepare 失败、重复 Close、在途 callback/token、Destroy 失败隔离代码路径；Start/Configure 失败、格式 fallback、平台错误注入真机待补。（FR28-05、06、08、10）
- [x] T011 [US2] 显式实验宏与独立watchdog真实回归，记录未知GPU完成时不走普通cleanup/fallback，外部有界退出；不将其设为通用mpv默认abort。证据：tests/lifecycle/t011-watchdog-03（normal PASS、experiment -6、missing-abort 变异被拒、external timeout）。（FR28-08）

## US3：行为与交付证据（P2）

- [~] T012 [US3] EOF/new-packet、bootstrap、reinit/fallback、seek入口真实RED后实现deferred reset并GREEN；GL和软件不适用路径无副作用。EOF RED/GREEN 已完成（red-t012-02、green-t005-26）；GL/软件/seek/reinit设备对照待T017。（FR28-07、10）
- [x] T013 [US3] 从Phase28实际源重跑HDR/SEI/AnnexB/优先级/Python回归，记录源绑定与失败诊断。证据：tests/regression/t013-02、build-runtime 四个 Python 单测全部通过。（FR28-11）
- [x] T014 [US3] 两clean完整/codec-only FFmpeg及mpv构建，原始SHA/ELF/编译链接输入核验，固定原五库/libplacebo，重建本轮准确清单。证据：build/evidence-final.json（FFmpeg e58d1f…、codec-only 57e6a7…、mpv 150f60…、libplacebo 4124ab…；compile inputs passed）。（FR28-09、11）
- [x] T015 [US3] 新独立CI checkout、完整文本输入索引、故障采集门禁、本地干净重放与精确提交预览；新SHA批准后才push。证据：分支 codex/phase28-validation，U1 后提交 52572fe33511f306aef22dd489077446009ddad3（已单独批准）；local-replay-09 passed=true；旧失败 2aea6b1、旧成功 6ca1274/ba586a6 保留。（FR28-11）
- [x] T016 [US3] 新Linux CI与artifact下载全索引/实际workflow/源/dirty状态核验，失败保留，不继承旧绿灯。run 39657429022 success；artifact 12372108316，ZIP SHA256 3db70a41…，135 文件全索引通过；旧失败 run 39635363231/旧成功 39636234441 保留。见 ci/CI-RUN.json。（FR28-11）
- [x] T017 [US3] 新诊断HAP/库/maps/实验宏绑定，deveco-cli构建安装，执行contracts/validation.md设备矩阵及外部watchdog验证。HAP 1a79a08d…，嵌入 libmpv/libavcodec 字节与构建产物核对一致；vk-pq/vk-switch/gl-pq/gl-pq-sw、Close/展示 Surface 顺序、keepScreen=false、独立 hang watchdog 均通过；GPU/Release 设备故障注入仍未验收。（FR28-12）
- [x] T018 [US3] 保屏false读回、空计划、进程停止；最终基线复核、manifest/REPORT/tasks/封存，未验收项目保持pending。keepScreen=false 回显、bm clean -d、force-stop（pidof 空）、REPORT/REVIEW-RESPONSE/tasks 与 seal.json 870f5066…；verify_handoff.py PASS。（FR28-01、12）

- [x] T019 [US2/US3] 独立审查 F1–F5、复审 R1–R3 与 U1 返修：Surface terminal 状态与拒绝新 producer、Stop/Destroy 有界终局、empty-current 历史 external release 等待、generic teardown 锁存、持久 owner 查询、watchdog 变异门禁、交接/seal 非循环一致性。U1 后 CI run 39657429022 success；证据 REVIEW-RESPONSE.md、green-t005-26、red-t005-12、t011-watchdog-06、verify_handoff.py。（FR28-08、10、11）
## 依赖、独立验收与实施顺序

T001→T002→T003→T004。

**基线 RED 先于所有对应源改动（2026-10-21 接手复核后明确）**：T005（US1）和 T008（US2）都必须先在未改动的 baseline 切片上编译成功并出现语义失败；T006 不得先于 T005，T009 不得先于 T008。两组 RED 可在同一轮独立建立，但各自的实现必须等自己的 RED 日志保存后才开始。

US1：T005→T006→T007；US2：T008→T009→T010→T011。**US1 的完整 consumer 交接 GREEN（T007）依赖 US2 的 Close/Destroy 收尾（T009/T010）**，因为旧 decoder 的 Stop/Destroy 必须在 Close 内完成且不能被推迟到新 producer 之后；在 US2 收尾未完成前，T007 只能记录部分顺序结果，不能宣称 US1 完整通过。反过来 US2 也不能用设备无告警替代 callback 回归。两者完成后 T012 整体验证，再 T013→T014→T015→（精确新 SHA 批准）→T016→T017→T018。

US1 不能用 US2 的 token 引用计数替代 GPU 顺序；每个 RED 先于其对应源改动；旧研究实验和 Phase27 绿灯不能替代本轮 RED/GREEN。

可并行的是只读输入检查、独立测试结果审阅；产品源整合串行，设备只有本执行会话操作。构建与CI不能提前绕过失败生命周期门禁。先验证最小成功序列，再补错误/EOF/重入边界，最后做全链验证；不得将实验fail-stop宣传成产品恢复策略。
