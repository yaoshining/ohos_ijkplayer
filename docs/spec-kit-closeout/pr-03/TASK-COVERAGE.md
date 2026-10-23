# 任务逐项覆盖台账

核对日2026-10-24。以原任务ID为键；“证据完成”仅指该行已记录的范围。旧任务文件不改写。局部任务以限定说明为准，不能把本表当正式验收全通过。

## specs/001-ffmpeg-ohcodec-producer/phase21/tasks.md

来源 S1；**未在此PR基线跟踪**，本轮仅登记本机实际规格与摘要，不能当作公开原件。

| 任务 | 原标记 | 当前分类 | 结论与承接 |
|---|---|---|---|
| T001 | `x` | 证据完成（原记录限定范围） | 读取实际人类授权、锁定三仓与旧封存，保存 out/phase21/authorization.json 和 boundary-start.json。<br>**当前：**原任务已勾选；本台账保留该执行范围，不新增构建、设备或发布通过。 |
| T002 | `x` | 证据完成（原记录限定范围） | 建立 out/phase21/ci/checkout 独立诊断分支，初始化本目录 spec/plan。<br>**当前：**原任务已勾选；本台账保留该执行范围，不新增构建、设备或发布通过。 |
| T003 | `x` | 证据完成（原记录限定范围） | 完成 out/phase21/research/{build,fonts}，形成 contracts/integration.md 和 data-model.md。<br>**当前：**原任务已勾选；本台账保留该执行范围，不新增构建、设备或发布通过。 |
| T004 | `x` | 证据完成（原记录限定范围） | 执行官方 prerequisite 和语义分析，保存 out/phase21/analysis.md 后进入实施。<br>**当前：**原任务已勾选；本台账保留该执行范围，不新增构建、设备或发布通过。 |
| T005 | `x` | 证据完成（原记录限定范围） | [US1] 在独立 tools/phase21/tests 编写工厂夹具，观察资源错误/Samba错误/分配/选项/初始化错误与重复销毁 RED，保存 out/phase21/tests。<br>**当前：**原任务已勾选；本台账保留该执行范围，不新增构建、设备或发布通过。 |
| T006 | `x` | 证据完成（原记录限定范围） | [US1] 实现 tools/phase21/integration.{c,h}，四规范绝对路径、失败 out=NULL、不可重设配置、已分配句柄恰好释放一次；通过 GREEN。<br>**当前：**原任务已勾选；本台账保留该执行范围，不新增构建、设备或发布通过。 |
| T007 | `x` | 证据完成（原记录限定范围） | [US1] 实现 tools/phase21/probe.c，真实 Samba/FFmpeg/mpv 顺序、重复/冲突/late 与运行日志。<br>**当前：**原任务已勾选；本台账保留该执行范围，不新增构建、设备或发布通过。 |
| T008 | `x` | 证据完成（原记录限定范围） | [US2] 在 tools/phase21/tests 编写资源准备/预检失败回归 RED；实现 resources.py 与固定字体/许可文件并通过 GREEN。<br>**当前：**原任务已勾选；本台账保留该执行范围，不新增构建、设备或发布通过。 |
| T009 | `x` | 证据完成（原记录限定范围） | [US2] 在 tools/phase21/probe.c 实现独立渲染线程与 RGB 捕获；render释放先于player；分别验证baseline/sub/OSD及字体日志，保留缺字体/缺字形负例。<br>**当前：**原任务已勾选；本台账保留该执行范围，不新增构建、设备或发布通过。 |
| T010 | `x` | 证据完成（原记录限定范围） | [US2] 在 tools/phase21/native.py 构建真实同源Linux软件栈，明确源码/系统库边界；记录真实maps/trace、只读资源、缓存EACCES与无HOME回退证据。<br>**当前：**原任务已勾选；本台账保留该执行范围，不新增构建、设备或发布通过。 |
| T011 | `x` | 证据完成（原记录限定范围） | [US3] 在 tools/phase21/build.py 绑定目标组件/头/静态LP输入，双根编译probe，核对ELF/版本导入/DT_NEEDED/map与原mpv能力不变。<br>**当前：**原任务已勾选；本台账保留该执行范围，不新增构建、设备或发布通过。 |
| T012 | `x` | 证据完成（原记录限定范围） | [US3] 新增 .github/workflows/phase21-integration.yml，发布前精确审查新增文件，执行真实CI；tools/phase21/collect.py 严格收集必要结果且拒绝源码pyc。<br>**当前：**原任务已勾选；本台账保留该执行范围，不新增构建、设备或发布通过。 |
| T013 | `x` | 证据完成（原记录限定范围） | [US3] 在 out/phase21/attempts 下载并独立复验CI提交、ZIP、索引全集、实际库/probe/渲染结果。<br>**当前：**原任务已勾选；本台账保留该执行范围，不新增构建、设备或发布通过。 |
| T014 | `x` | 证据完成（原记录限定范围） | 写 docs/producer-phase21-report.md、out/phase21/manifest.json、handoff.json 与设备清单，复验产品边界，生成只含本轮必要新证据的索引/seal并独立验证。<br>**当前：**原任务已勾选；本台账保留该执行范围，不新增构建、设备或发布通过。 |

## specs/001-ffmpeg-ohcodec-producer/phase22/tasks.md

来源 S2；**未在此PR基线跟踪**，本轮仅登记本机实际规格与摘要，不能当作公开原件。

| 任务 | 原标记 | 当前分类 | 结论与承接 |
|---|---|---|---|
| T001 | `x` | 证据完成（原记录限定范围） | 新out/phase22/authorization.json与boundary-start.json，用户指定真机身份核对。<br>**当前：**原任务已勾选；本台账保留该执行范围，不新增构建、设备或发布通过。 |
| T002 | `x` | 证据完成（原记录限定范围） | devecocli生成out/phase22/app独立bundle；Spec Kit官方plan/tasks初始化。<br>**当前：**原任务已勾选；本台账保留该执行范围，不新增构建、设备或发布通过。 |
| T003 | `x` | 证据完成（原记录限定范围） | 完成research.md、合同/语义分析及implement prerequisite。<br>**当前：**原任务已勾选；本台账保留该执行范围，不新增构建、设备或发布通过。 |
| T004 | `x` | 证据完成（原记录限定范围） | tools/tests先验证未知/宿主case拒绝RED，再实现独立CLI分派GREEN。<br>**当前：**原任务已勾选；本台账保留该执行范围，不新增构建、设备或发布通过。 |
| T005 | `x` | 证据完成（原记录限定范围） | 绑定7库/头/工具，双根编译；真机临时根加载/maps/文件SHA。<br>**当前：**原任务已勾选；本台账保留该执行范围，不新增构建、设备或发布通过。 |
| T006 | ` ` | 待验收（部分覆盖） | 真机init/repeat/conflict和资源缺失/坏字体/权限/缓存路径。<br>**当前：**E12确认init/repeat/conflict、五项resource错误已验；symlink创建EACCES先于validator，不能记验证器通过。 |
| T007 | `x` | 证据完成（原记录限定范围） | TDD验证播放选项与帧/EOF判定；准备固定H264/HEVC/音频/字幕夹具。<br>**当前：**原任务已勾选；本台账保留该执行范围，不新增构建、设备或发布通过。 |
| T008 | ` ` | 替代或范围调整 | 新建临时SMB服务，真实登录/读/seek/重连与服务日志。<br>**当前：**初次SMB打开失败保留；Phase23最低方言夹具修复后的读/seek/重连矩阵承接，后续Phase31正常NAS短操作覆盖。 |
| T009 | `x` | 证据完成（原记录限定范围） | 独立HAP的Surface与GPU/音频工厂，RED/GREEN，devecocli构建安装。<br>**当前：**原任务已勾选；本台账保留该执行范围，不新增构建、设备或发布通过。 |
| T010 | ` ` | 待验收（部分覆盖） | 真机OHCodec H264/HEVC、GL/Vulkan、Surface循环、字幕OSD/CJK、seek/EOF/同步/异常释放，逐项原始证据或明确阻塞。<br>**当前：**E12区分Vulkan、CJK/OSD和逻辑时钟已验，默认GL/资源增长失败由后继修复；不将整个宽矩阵、物理声画或HDR批量记通过。 |
| T011 | ` ` | 证据完成 | 独立CI（适用源码验证）与产物下载；签名/设备结果不从CI继承。<br>**当前：**E11为snapshots/03后补：4ad9c4ce / run39366120567，56项ZIP/54源文件核验、12宿主测试；无新真机运行。 |
| T012 | `x` | 证据完成（原记录限定范围） | 报告/manifest/handoff/逐项状态，边界复验与新封存独立校验。<br>**当前：**原任务已勾选；本台账保留该执行范围，不新增构建、设备或发布通过。 |

## specs/001-ffmpeg-ohcodec-producer/phase23/tasks.md

来源 S3；本PR基线已跟踪。

| 任务 | 原标记 | 当前分类 | 结论与承接 |
|---|---|---|---|
| T001 | `x` | 证据完成（原记录限定范围） | 核实人类授权并在本地保存授权依据。<br>**当前：**原任务已勾选；本台账保留该执行范围，不新增构建、设备或发布通过。 |
| T002 | `x` | 证据完成（原记录限定范围） | 核验Phase22/03、三仓与候选边界，保存out/phase23/previous-seal-verification.json及boundary-verification.json。（FR-001）<br>**当前：**原任务已勾选；本台账保留该执行范围，不新增构建、设备或发布通过。 |
| T003 | `x` | 证据完成（原记录限定范围） | 执行官方初始化并形成spec/plan/data-model/contracts/quickstart于specs/001-ffmpeg-ohcodec-producer/phase23。<br>**当前：**原任务已勾选；本台账保留该执行范围，不新增构建、设备或发布通过。 |
| T004 | `x` | 证据完成（原记录限定范围） | 汇总两项源码研究于specs/001-ffmpeg-ohcodec-producer/phase23/research.md，完成只读语义分析与官方prerequisite。（FR-002）<br>**当前：**原任务已勾选；本台账保留该执行范围，不新增构建、设备或发布通过。 |
| T005 | `x` | 证据完成（原记录限定范围） | 复制独立应用/工具至out/phase23/app及tools，绑定输入且不读keys内容。（FR-001、FR-006）<br>**当前：**原任务已勾选；本台账保留该执行范围，不新增构建、设备或发布通过。 |
| T006 | `x` | 证据完成（原记录限定范围） | 在out/phase23/tools建立采样与脱敏日志回归，连接指定设备，仅操作诊断bundle。（FR-007）<br>**当前：**原任务已勾选；本台账保留该执行范围，不新增构建、设备或发布通过。 |
| T007 | `x` | 证据完成（原记录限定范围） | [US1] 在out/phase23/tools/smb_server.py增加无凭据的数字协议阶段观测，先测试并保存out/phase23/tests/smb-observation-red.log。（FR-002、FR-003）<br>**当前：**原任务已勾选；本台账保留该执行范围，不新增构建、设备或发布通过。 |
| T008 | `x` | 证据完成（原记录限定范围） | [US1] 运行旧库目标RED并定位失败阶段，保存out/phase23/device-smb-01.log。（SC-001）<br>**当前：**原任务已勾选；本台账保留该执行范围，不新增构建、设备或发布通过。 |
| T009 | `x` | 证据完成（原记录限定范围） | [US1] 在out/phase23/input-package/sources 或 ffmpeg-input/source或工具层实现已证实根因的最小补丁；保存补丁及正常/边界/错误回归。（FR-002、FR-003）<br>**当前：**原任务已勾选；本台账保留该执行范围，不新增构建、设备或发布通过。 |
| T010 | `x` | 证据完成（原记录限定范围） | [US1] 在out/phase23/build构建受影响链双clean、绑定实际库与目标maps。（FR-006）<br>**当前：**原任务已勾选；本台账保留该执行范围，不新增构建、设备或发布通过。 |
| T011 | `x` | 证据完成（原记录限定范围） | [US1] 真机验证正确/错误认证、8MiB、六段seek、不可达端口及显式断开后重新打开，保存out/phase23/experiments/smb-matrix-06 和 final-combination-10。（SC-001）<br>**当前：**原任务已勾选；本台账保留该执行范围，不新增构建、设备或发布通过。 |
| T012 | `x` | 证据完成（原记录限定范围） | [US2] 在out/phase23/app采集至少3轮热身+10轮观察，每轮before/playing/destroyed/settled；失败读取不记0，固定和新Surface均运行，保存out/phase23/experiments/gpu-baseline-03 和 new-surface-baseline-08。（FR-004、SC-002）<br>**当前：**原任务已勾选；本台账保留该执行范围，不新增构建、设备或发布通过。 |
| T013 | `x` | 证据完成（原记录限定范围） | [US2] 根据所有权源码与阶段观测定位根因，先回归RED再在out/phase23/input-package/sources 或 ffmpeg-input/source修最小释放/生命周期路径。（FR-002、FR-004）<br>**当前：**原任务已勾选；本台账保留该执行范围，不新增构建、设备或发布通过。 |
| T014 | `x` | 证据完成（原记录限定范围） | [US2] 独立双clean重建受影响mpv/依赖，并绑定out/phase23/build库与maps。（FR-006）<br>**当前：**原任务已勾选；本台账保留该执行范围，不新增构建、设备或发布通过。 |
| T015 | `x` | 证据完成（原记录限定范围） | [US2] 重复同样目标循环与无播放器对照，量化稳定期、延迟回收及未解释增长，保存out/phase23/experiments/release-fix-09 和 final-combination-10。（SC-002）<br>**当前：**原任务已勾选；本台账保留该执行范围，不新增构建、设备或发布通过。 |
| T016 | `x` | 证据完成（原记录限定范围） | [US3] 在out/phase23/app运行新进程GL-first与同Surface VK→GL、GL→VK→GL对照，保存out/phase23/experiments/gl-config-04。（FR-005）<br>**当前：**原任务已勾选；本台账保留该执行范围，不新增构建、设备或发布通过。 |
| T017 | `x` | 证据完成（原记录限定范围） | [US3] 来源层格式/恢复契约先RED，再修改out/phase23/input-package/sources 或 ffmpeg-input/source的窗口实际所有者，保存补丁；应用不代设SET_FORMAT。（FR-002、FR-005）<br>**当前：**原任务已勾选；本台账保留该执行范围，不新增构建、设备或发布通过。 |
| T018 | `x` | 证据完成（原记录限定范围） | [US3] 真机默认GL H264硬/软解、失败恢复、销毁重建与显式RGBA8对照，保存out/phase23/experiments/final-combination-10、final-gl-recovery-11、final-gl-stop-12、final-surface-pixels-13。（SC-003）<br>**当前：**原任务已勾选；本台账保留该执行范围，不新增构建、设备或发布通过。 |
| T019 | ` ` | 证据完成 | 复核新来源/补丁/工具链、ABI/导出、库/源/设备绑定；在out/phase23/ci准备可审阅提交并按新授权边界处理CI和下载复验。（FR-006、FR-008）<br>**当前：**3e7e9e34 / run39373185636、108项artifact核验及cleanup-final；保留原提交前状态。E1/E2。 |
| T020 | ` ` | 证据完成 | 停止独立诊断和临时服务，复核旧封存/三仓/候选边界，在out/phase23/manifest.json和seal.json逐项记录通过/失败/未测。（FR-001、FR-007、SC-004）<br>**当前：**3e7e9e34 / run39373185636、108项artifact核验及cleanup-final；保留原提交前状态。E1/E2。 |
| T021 | `x` | 证据完成（原记录限定范围） | 补齐GL硬/软解真实主动停止（12），与Vulkan停止→GL恢复（11）分别验收。<br>**当前：**原任务已勾选；本台账保留该执行范围，不新增构建、设备或发布通过。 |
| T022 | `x` | 证据完成（原记录限定范围） | 修正探针vp/px接线，SurfaceSize真实函数边界回归与13目标八场景；16次NativeWindow geometry均匹配实际2880×1620像素，截图复核同布局。<br>**当前：**原任务已勾选；本台账保留该执行范围，不新增构建、设备或发布通过。 |

## specs/001-ffmpeg-ohcodec-producer/phase24/tasks.md

来源 S4；本PR基线已跟踪。

| 任务 | 原标记 | 当前分类 | 结论与承接 |
|---|---|---|---|
| T001 | `x` | 证据完成（原记录限定范围） | 复核冻结边界与授权，保存out/phase24/baseline-start.json及authorization.json（FR-001/009）。<br>**当前：**原任务已勾选；本台账保留该执行范围，不新增构建、设备或发布通过。 |
| T002 | `x` | 证据完成（原记录限定范围） | 完成spec/plan/research/data-model/contracts/quickstart与官方脚本证据，目录specs/001-ffmpeg-ohcodec-producer/phase24（FR-010）。<br>**当前：**原任务已勾选；本台账保留该执行范围，不新增构建、设备或发布通过。 |
| T003 | `x` | 证据完成（原记录限定范围） | 运行官方prerequisite并人工跨文档语义分析，保存out/phase24/spec-analysis.md。<br>**当前：**原任务已勾选；本台账保留该执行范围，不新增构建、设备或发布通过。 |
| T004 | `x` | 证据完成（原记录限定范围） | 从out/phase23/app复制独立out/phase24/app，排除构建缓存和旧私有SMB夹具，校验七库相同（FR-001/008）。<br>**当前：**原任务已勾选；本台账保留该执行范围，不新增构建、设备或发布通过。 |
| T005 | `x` | 证据完成（原记录限定范围） | [US1] 在out/phase24/tests/test_contract.py先写短时间/EOF/缺失值/fallback/时钟/中断负例与正常窗口，观察RED（FR-003/004）。<br>**当前：**原任务已勾选；本台账保留该执行范围，不新增构建、设备或发布通过。 |
| T006 | `x` | 证据完成（原记录限定范围） | [US1] 在out/phase24/tests先写中文路径/编码URL/凭据错误日志脱敏RED（FR-002/005）。<br>**当前：**原任务已勾选；本台账保留该执行范围，不新增构建、设备或发布通过。 |
| T007 | `x` | 证据完成（原记录限定范围） | [US1] 实现out/phase24/tools/contract.py及app C++日志策略/低频采样/连续判定，运行GREEN（FR-003/004/005）。<br>**当前：**原任务已勾选；本台账保留该执行范围，不新增构建、设备或发布通过。 |
| T008 | `x` | 证据完成（原记录限定范围） | [US1] 实现out/phase24/tools/nas_preflight.py精确文件只读元数据预检和外部配置加载，不遍历目录（FR-002）。<br>**当前：**原任务已勾选；本台账保留该执行范围，不新增构建、设备或发布通过。 |
| T009 | `x` | 证据完成（原记录限定范围） | [US1] out/phase24/app接入独立短seek/恢复用例与3600秒真实播放场景，源码/HAP/maps绑定（FR-003/008）。<br>**当前：**原任务已勾选；本台账保留该执行范围，不新增构建、设备或发布通过。 |
| T010 | ` ` | 替代或范围调整 | [US1] 用户凭据/设备就绪后执行指定文件预检、短测、连续长播，结果out/phase24/experiments（FR-002/003/004/009）。<br>**当前：**NAS测试已推进但旧60分钟未通过；Phase31七短场景及一次SDR现场观察不等于长播。用户取消60分钟作为前置，不重跑、不调查后台来源作为接入条件。 |
| T011 | `x` | 证据完成（原记录限定范围） | [P] [US2] out/phase24/tests/test_hdr_chart.py固定标准码值/边界/非8bit扩展的RED（FR-006）。<br>**当前：**原任务已勾选；本台账保留该执行范围，不新增构建、设备或发布通过。 |
| T012 | `x` | 证据完成（原记录限定范围） | [US2] out/phase24/tools/generate_hdr_chart.py实现并GREEN；编码三类样本，ffprobe/解码像素独立验证，out/phase24/fixtures/hdr（FR-006）。<br>**当前：**原任务已勾选；本台账保留该执行范围，不新增构建、设备或发布通过。 |
| T013 | `x` | 证据完成（原记录限定范围） | [US2] out/phase24/app接入三类×GL/VK×OHCodec/software、同实例HDR/SDR恢复与同transfer源切换；现有日志/属性/显示能力，禁止竞态getter（FR-007）。<br>**当前：**原任务已勾选；本台账保留该执行范围，不新增构建、设备或发布通过。 |
| T014 | `x` | 证据完成（原记录限定范围） | [US2] 指定电视执行矩阵并保存分层证据out/phase24/experiments，缺失值未测；稳定画面后才请求人工确认（FR-007/009）。<br>**当前：**原任务已勾选；本台账保留该执行范围，不新增构建、设备或发布通过。 |
| T015 | `x` | 证据完成（原记录限定范围） | [US3] out/phase24/app执行devecocli构建、固化源码/HAP/七库绑定，保留实际失败（FR-008）。<br>**当前：**原任务已勾选；本台账保留该执行范围，不新增构建、设备或发布通过。 |
| T016 | ` ` | 替代或范围调整 | [US3] 如库问题真机复现，先报告、独立来源RED/最小修复/双clean/新maps，out/phase24/experiments；无实际问题则不改七库（FR-008）。<br>**当前：**HDR元数据及缓存修复由Phase27承接；Vulkan安全释放由Phase28及后继承接。旧库诊断失败保留。 |
| T017 | ` ` | 证据完成（限定） | [US3] out/phase24/ci隔离源码/规范/脱敏结果，运行测试/CI并复核制品，不含HAP/凭据/私人影片（FR-005/010）。<br>**当前：**CI6fe31c94 / run39418975083及阶段报告已完成；NAS/HDR完整验收false，不把阶段执行完写成全部功能通过。E3。 |
| T018 | ` ` | 证据完成（限定） | [US3] out/phase24/REPORT.md及manifest.json分项结论，最终边界复核、seal；人工/正式交付未通过保持pending（FR-001/009/010）。<br>**当前：**CI6fe31c94 / run39418975083及阶段报告已完成；NAS/HDR完整验收false，不把阶段执行完写成全部功能通过。E3。 |

## specs/001-ffmpeg-ohcodec-producer/phase25/tasks.md

来源 S5；**未在此PR基线跟踪**，本轮仅登记本机实际规格与摘要，不能当作公开原件。

| 任务 | 原标记 | 当前分类 | 结论与承接 |
|---|---|---|---|
| T001 | `x` | 证据完成（原记录限定范围） | 核验授权和边界，保存 out/phase25/authorization.json、boundary-verification.json。<br>**当前：**原任务已勾选；本台账保留该执行范围，不新增构建、设备或发布通过。 |
| T002 | `x` | 证据完成（原记录限定范围） | 完成 specs/001-ffmpeg-ohcodec-producer/phase25 的 spec/plan/research/contracts。<br>**当前：**原任务已勾选；本台账保留该执行范围，不新增构建、设备或发布通过。 |
| T003 | `x` | 证据完成（原记录限定范围） | 复制独立诊断到 out/phase25/app，保留七库，准备 tests 与 private 权限。<br>**当前：**原任务已勾选；本台账保留该执行范围，不新增构建、设备或发布通过。 |
| T004 | `x` | 证据完成（原记录限定范围） | [US1] 在 out/phase25/tests/test_timeline.cpp 先写并运行 RED，涵盖阻塞、短写、错误、并发seq、时钟与关闭。<br>**当前：**原任务已勾选；本台账保留该执行范围，不新增构建、设备或发布通过。 |
| T005 | `x` | 证据完成（原记录限定范围） | [US1] 实现 out/phase25/app/entry/src/main/cpp/phase25_timeline.h 与 napi.cpp、phase25_runner.inc，运行 GREEN。<br>**当前：**原任务已勾选；本台账保留该执行范围，不新增构建、设备或发布通过。 |
| T006 | `x` | 证据完成（原记录限定范围） | [US1] 先RED后GREEN实现 out/phase25/tools/analyze_timeline.py 和 tests/test_analysis.py，缺行/截断/重复/open query 均不能完整通过。<br>**当前：**原任务已勾选；本台账保留该执行范围，不新增构建、设备或发布通过。 |
| T007 | `x` | 证据完成（原记录限定范围） | [US2] 在 out/phase25/tests 写状态/迟到事件 RED，最小实现 ets/lifecycle/Timeline.ets 与 EntryAbility.ets、Index.ets 后 GREEN。<br>**当前：**原任务已勾选；本台账保留该执行范围，不新增构建、设备或发布通过。 |
| T008 | `x` | 证据完成（原记录限定范围） | [US3] devecocli 构建 out/phase25/app，绑定 source/HAP/七库至 out/phase25/experiments。<br>**当前：**原任务已勾选；本台账保留该执行范围，不新增构建、设备或发布通过。 |
| T009 | `x` | 证据完成（原记录限定范围） | [US3] 保存 out/phase25/presence-setting.json 当前值；短场景及外部观察，分析缺口；按结果决定是否长播。<br>**当前：**原任务已勾选；本台账保留该执行范围，不新增构建、设备或发布通过。 |
| T010 | `x` | 证据完成（原记录限定范围） | [US3] 确认系统设置不变、关闭应用保屏、清理派生凭据和停止独立诊断，写 out/phase25/cleanup.json。<br>**当前：**原任务已勾选；本台账保留该执行范围，不新增构建、设备或发布通过。 |
| T011 | `x` | 证据完成（原记录限定范围） | 重新核对边界并保存 specs/001-ffmpeg-ohcodec-producer/phase25/REPORT.md、out/phase25 的 index/seal，待验项保持待验。<br>**当前：**原任务已勾选；本台账保留该执行范围，不新增构建、设备或发布通过。 |

## specs/001-ffmpeg-ohcodec-producer/phase26/tasks.md

来源 S6；**未在此PR基线跟踪**，本轮仅登记本机实际规格与摘要，不能当作公开原件。

| 任务 | 原标记 | 当前分类 | 结论与承接 |
|---|---|---|---|
| T001 | `x` | 证据完成（原记录限定范围） | 核对人类授权和 out/phase26/authorization.json，保留旧封存及边界预检（FR01）。<br>**当前：**原任务已勾选；本台账保留该执行范围，不新增构建、设备或发布通过。 |
| T002 | `x` | 证据完成（原记录限定范围） | 完成 spec/plan/research/data-model/contracts/quickstart 与官方 setup、checklists（FR01–08）。<br>**当前：**原任务已勾选；本台账保留该执行范围，不新增构建、设备或发布通过。 |
| T003 | `x` | 证据完成（原记录限定范围） | 执行官方 prerequisites 与语义审查 out/phase26/analysis.md。<br>**当前：**原任务已勾选；本台账保留该执行范围，不新增构建、设备或发布通过。 |
| T004 | `x` | 证据完成（原记录限定范围） | [US1] 创建 out/phase26/ci/checkout 隔离 clone 并按来源允许列表复制实际 Phase25 文件（FR02）。<br>**当前：**原任务已勾选；本台账保留该执行范围，不新增构建、设备或发布通过。 |
| T005 | `x` | 证据完成（原记录限定范围） | [US1] 编写 tools/phase26/tests/test_runner.py，先执行缺实现/漂移/子进程失败/隐私哨兵 RED（FR03）。<br>**当前：**原任务已勾选；本台账保留该执行范围，不新增构建、设备或发布通过。 |
| T006 | `x` | 证据完成（原记录限定范围） | [US1] 实现 tools/phase26/runner.py、collect.py，sourceRecord只接受允许路径普通非symlink文件及摘要一致（FR02/03）。<br>**当前：**原任务已勾选；本台账保留该执行范围，不新增构建、设备或发布通过。 |
| T007 | `x` | 证据完成（原记录限定范围） | [US1] 新增真实 phase25_mpv.h/sampling.cpp stub-link 测试并执行16Python/原生ASan+UBSan；覆盖与产品缺陷RED分别记（FR02）。<br>**当前：**原任务已勾选；本台账保留该执行范围，不新增构建、设备或发布通过。 |
| T008 | `x` | 证据完成（原记录限定范围） | [US1] 创建工作流/中文说明和精确提交预览 out/phase26/ci/push-preview.md；获新SHA批准后运行LinuxCI与下载校验，未批准保留pending（FR03/SC01）。<br>**当前：**原任务已勾选；本台账保留该执行范围，不新增构建、设备或发布通过。 |
| T009 | `x` | 证据完成（原记录限定范围） | [US2] 新增 out/phase26/tests/test_hdr.py、tools/hdr_gate.py，对真实绑定日志缺MDM/CLL保留失败，missing不同于0（FR04）。<br>**当前：**原任务已勾选；本台账保留该执行范围，不新增构建、设备或发布通过。 |
| T010 | `x` | 证据完成（原记录限定范围） | [US2] 新增首帧metadata/consumer所有权合同回归RED，再实现 out/phase26/app 内实际桥（FR05）。<br>**当前：**原任务已勾选；本台账保留该执行范围，不新增构建、设备或发布通过。 |
| T011 | `x` | 证据完成（原记录限定范围） | [US2] devecocli构建原七库HAP，绑定SHA/maps/夹具并执行原PQ/HLG/SDR软硬首帧串行真机诊断，记录应用保屏（FR04–06/SC02）。<br>**当前：**原任务已勾选；本台账保留该执行范围，不新增构建、设备或发布通过。 |
| T012 | `x` | 证据完成（原记录限定范围） | [US3] 原七库GL/Vulkan各同实例PQ1000→PQ2000→HLG→SDR，分析静态metadata更新与pending输出层（FR07）。<br>**当前：**原任务已勾选；本台账保留该执行范围，不新增构建、设备或发布通过。 |
| T013 | `x` | 证据完成（原记录限定范围） | [US3] 对需要改库的最小范围写 out/phase26/HDR-NEXT.md，现场场景就绪再请求人眼；无证保持pending（FR07）。<br>**当前：**原任务已勾选；本台账保留该执行范围，不新增构建、设备或发布通过。 |
| T014 | `x` | 证据完成（原记录限定范围） | [US3] 清理运行计划/停止应用，重核边界，写REPORT/manifest与新快照（FR08/SC03）。<br>**当前：**原任务已勾选；本台账保留该执行范围，不新增构建、设备或发布通过。 |

## specs/001-ffmpeg-ohcodec-producer/phase27/tasks.md

来源 S7；**未在此PR基线跟踪**，本轮仅登记本机实际规格与摘要，不能当作公开原件。

| 任务 | 原标记 | 当前分类 | 结论与承接 |
|---|---|---|---|
| T001 | `x` | 证据完成（原记录限定范围） | 核验直接授权与旧封存，记录 out/phase27/authorization.json、phase26-precheck.json 和 boundary-verification.json。（FR06/08）<br>**当前：**原任务已勾选；本台账保留该执行范围，不新增构建、设备或发布通过。 |
| T002 | `x` | 证据完成（原记录限定范围） | 运行官方setup-plan/setup-tasks，完成本目录spec/plan/research/data-model/contracts/quickstart。（全部FR）<br>**当前：**原任务已勾选；本台账保留该执行范围，不新增构建、设备或发布通过。 |
| T003 | `x` | 证据完成（原记录限定范围） | 完成本目录analysis.md语义审查与官方prerequisite；复制并核验 out/phase27/ffmpeg-input/source、input-package、build-runtime。（FR06/07）<br>**当前：**原任务已勾选；本台账保留该执行范围，不新增构建、设备或发布通过。 |
| T004 | `x` | 证据完成（原记录限定范围） | [US1] 在 out/phase27/tests 建立真实FFmpeg SEI与旧ohdec连接RED；覆盖独立MDM/CLL、坏SEI、PTS/IRAP/flush/事务/已有side-data。（FR01–03）<br>**当前：**原任务已勾选；本台账保留该执行范围，不新增构建、设备或发布通过。 |
| T005 | `x` | 证据完成（原记录限定范围） | [US1] 在 out/phase27/ffmpeg-input/source/libavcodec 实现内部HDR helper和ohdec连接；补configure/Makefile依赖，保存补丁与GREEN。（FR01–03）<br>**当前：**原任务已勾选；本台账保留该执行范围，不新增构建、设备或发布通过。 |
| T006 | `x` | 证据完成（原记录限定范围） | [US1] OOM/重排/多slice/分片失败/DOVI隔离和OHCodec-only真实链接，记录 out/phase27/tests。（FR01–03/07）<br>**当前：**原任务已勾选；本台账保留该执行范围，不新增构建、设备或发布通过。 |
| T007 | `x` | 证据完成（原记录限定范围） | [P] [US2] 在 out/phase27/tests/mpv 建立原函数同PQ缓存与陈旧来源覆盖RED，逐字段及tone-map负例。（FR04）<br>**当前：**原任务已勾选；本台账保留该执行范围，不新增构建、设备或发布通过。 |
| T008 | `x` | 证据完成（原记录限定范围） | [US2] 最小修改 out/phase27/input-package/sources/mpv/video/out/ohos_common.c，真实调用链GREEN及来源绑定。（FR04）<br>**当前：**原任务已勾选；本台账保留该执行范围，不新增构建、设备或发布通过。 |
| T009 | `x` | 证据完成（原记录限定范围） | [US3] 完成 out/phase27/research/vulkan-lifetime.md 与实际函数所有权基线。（FR05）<br>**当前：**原任务已勾选；本台账保留该执行范围，不新增构建、设备或发布通过。 |
| T010 | `x` | 证据完成（原记录限定范围） | [US3] 在本轮codec/mpv副本增加有界monotonic/seq/owner追踪；probe独立sink覆盖最后destroy，tests验证日志完整性。（FR05）<br>**当前：**原任务已勾选；本台账保留该执行范围，不新增构建、设备或发布通过。 |
| T011 | `x` | 证据完成（原记录限定范围） | [US3] 根据 out/phase27/experiments 实测事件确认根因；如可安全修复则真实RED/最小修复/GREEN及目标复验，否则报告具体pending。（FR05/08）<br>**当前：**原任务已勾选；本台账保留该执行范围，不新增构建、设备或发布通过。 |
| T012 | `x` | 证据完成（原记录限定范围） | [US4] 固定所有实际工具/模块与依赖、源码补丁清单到 out/phase27，完成两个fresh FFmpeg及OHCodec-only配置。（FR06/07）<br>**当前：**原任务已勾选；本台账保留该执行范围，不新增构建、设备或发布通过。 |
| T013 | `x` | 证据完成（原记录限定范围） | [US4] 比较codec ABI及原五库闭包，更新本轮input-package；两个fresh mpv/libplacebo及实际Ninja编译输入核验。（FR06/07）<br>**当前：**原任务已勾选；本台账保留该执行范围，不新增构建、设备或发布通过。 |
| T014 | `x` | 证据完成（原记录限定范围） | [US4] 复制诊断app到 out/phase27/app，新增连续同PQ/完整sink与本轮绑定；devecocli新HAP构建。（FR04/05/08）<br>**当前：**原任务已勾选；本台账保留该执行范围，不新增构建、设备或发布通过。 |
| T015 | `x` | 证据完成（原记录限定范围） | [US4] 真机direct硬软、同instance同PQ、GL/Vulkan switch含销毁trace与应用保屏回读，记录 out/phase27/experiments。（FR01–08）<br>**当前：**原任务已勾选；本台账保留该执行范围，不新增构建、设备或发布通过。 |
| T016 | `x` | 证据完成（原记录限定范围） | [US4] 准备 out/phase27/ci 精确提交/文件预览；新SHA获人类批准才push，验证本轮CI及下载ZIP全部索引。（FR07/08）<br>**当前：**原任务已勾选；本台账保留该执行范围，不新增构建、设备或发布通过。 |
| T017 | `x` | 证据完成（原记录限定范围） | 设备空计划/停止/保屏false回读、产品与旧封存复验，记录 out/phase27/cleanup.json。（FR06/08）<br>**当前：**原任务已勾选；本台账保留该执行范围，不新增构建、设备或发布通过。 |
| T018 | `x` | 证据完成（原记录限定范围） | 完成本目录REPORT.md及 out/phase27 报告/manifest/新封存，区分所有证据层和pending。（全部FR）<br>**当前：**原任务已勾选；本台账保留该执行范围，不新增构建、设备或发布通过。 |

## specs/001-ffmpeg-ohcodec-producer/phase28-device-validation/tasks.md

来源 S8；**未在此PR基线跟踪**，本轮仅登记本机实际规格与摘要，不能当作公开原件。

| 任务 | 原标记 | 当前分类 | 结论与承接 |
|---|---|---|---|
| D001 | `x` | 证据完成（原记录限定范围） | 读取适用规范/技能，核对三仓、12产物、旧seal、基线SHA，建立独立目录。<br>**当前：**原任务已勾选；本台账保留该执行范围，不新增构建、设备或发布通过。 |
| D002 | `x` | 证据完成（原记录限定范围） | 形成规格/计划/七组矩阵，区分abort与retained、Release分级，运行Spec Kit setup。<br>**当前：**原任务已勾选；本台账保留该执行范围，不新增构建、设备或发布通过。 |
| D003 | `x` | 证据完成（原记录限定范围） | 有界重连并核对设备身份/当前使用状态；设备不可用保存阻塞。<br>**当前：**原任务已勾选；本台账保留该执行范围，不新增构建、设备或发布通过。 |
| D004 | `x` | 证据完成（原记录限定范围） | 为preflight UNSAFE→generic teardown编译真实函数并观察语义RED；注入关闭/次数/真实错误优先等回归先RED。<br>**当前：**原任务已勾选；本台账保留该执行范围，不新增构建、设备或发布通过。 |
| D005 | `x` | 证据完成（原记录限定范围） | 最小实现UNSAFE单调性（若RED确认）及诊断注入/日志，GREEN及负例门禁。<br>**当前：**原任务已勾选；本台账保留该执行范围，不新增构建、设备或发布通过。 |
| D006 | `x` | 证据完成（原记录限定范围） | 同consumer身份日志与受控拒绝验证，先RED后实现，force-window诊断保留。<br>**当前：**原任务已勾选；本台账保留该执行范围，不新增构建、设备或发布通过。 |
| D007 | `x` | 证据完成（原记录限定范围） | 隔离retained/abort及无注入验证构建，保留Python回归、源码/工具链/库绑定。<br>**当前：**原任务已勾选；本台账保留该执行范围，不新增构建、设备或发布通过。 |
| D008 | `x` | 证据完成（原记录限定范围） | 独立诊断HAP构建与内库/设备maps绑定。<br>**当前：**原任务已勾选；本台账保留该执行范围，不新增构建、设备或发布通过。 |
| D009 | `x` | 证据完成（原记录限定范围） | GPU/Release三种诊断分类、外部有界终止与新进程恢复真机证据；父级修复后以新HAP重测，证据见 `out/phase28-device-validation/resume-04/device/`。<br>**当前：**原任务已勾选；本台账保留该执行范围，不新增构建、设备或发布通过。 |
| D010 | `x` | 证据完成（原记录限定范围） | 同consumer正常交接及交错拒绝真机证据。<br>**当前：**不无条件继承旧同consumer措辞；以Phase30 A02同owner/NativeImage/稳定consumer身份的3次顺序交接及B03单实例受控真实交错为限定已验范围，seek=-12不是成功seek，任意多实例/极端并发仍待验。 |
| D011 | `x` | 证据完成（原记录限定范围） | 正常Vulkan/GL/软件回归、keepScreen=false/计划空/进程退出、最终边界与报告；Vulkan/GL/软件均加载新normal HAP，应用保屏readback=false，计划为空。<br>**当前：**原任务已勾选；本台账保留该执行范围，不新增构建、设备或发布通过。 |
| D012 | `x` | 证据完成（原记录限定范围） | 保存父级最小候选方案；真实 gpu_next.uninit + hwdec_devices_destroy 复现精确断言 RED（编译通过、SIGABRT 与目标断言匹配）。<br>**当前：**原任务已勾选；本台账保留该执行范围，不新增构建、设备或发布通过。 |
| D013 | `x` | 证据完成（原记录限定范围） | 审计 dispatch/callback/talloc/global 依赖，最小终止屏障实现及完整父链 GREEN/内层return负例，普通与SAFE_RELEASE_ERROR保持清理；真实源函数宿主测试 `tests/parent-chain/red-current-v3` → `green-parentfix-e`，提取真实 `misc/dispatch.c`、`vo_thread`、`uninit_video_out`/`mp_destroy`，含 late-uninit、实验abort、仅内层return负例、真实 vo_thread 提前销毁负例，以及 NativeImage/FFmpeg 回调与 global/log/config 依赖审计；F1 返修加入关键销毁即时事件、观察快照和 queue 前移负例。<br>**当前：**原任务已勾选；本台账保留该执行范围，不新增构建、设备或发布通过。 |
| D014 | `x` | 证据完成（原记录限定范围） | 新三套源/宏/库/HAP绑定，重复Python门禁，真机retained/abort/边界挂起及恢复，Release与normal Vulkan/GL/软件回归，保护边界和应用收尾；HAP绑定 `artifacts-parentfix/manifest.json`，设备分析 `resume-04/device/analysis.json`，边界 `resume-04/boundary-after.json`。<br>**当前：**原任务已勾选；本台账保留该执行范围，不新增构建、设备或发布通过。 |

## specs/001-ffmpeg-ohcodec-producer/phase28-parent-chain-ci/tasks.md

来源 S9；本PR基线已跟踪。

| 任务 | 原标记 | 当前分类 | 结论与承接 |
|---|---|---|---|
| C001 | `x` | 证据完成（原记录限定范围） | 阅读宪章/Spec Kit 实施技能、实际 prerequisite、原规格和复审材料；核对远端基线。<br>**当前：**原任务已勾选；本台账保留该执行范围，不新增构建、设备或发布通过。 |
| C002 | `x` | 证据完成（原记录限定范围） | 写 CI 门禁回归并保存缺 runner 的真实 RED；实现结果/变异/输入/上传边界门禁，9 项 GREEN。<br>**当前：**原任务已勾选；本台账保留该执行范围，不新增构建、设备或发布通过。 |
| C003 | `x` | 证据完成（原记录限定范围） | 固定源子集、许可证、来源映射、真实父链与 FFmpeg 测试；新增 11 项合成清理测试。<br>**当前：**原任务已勾选；本台账保留该执行范围，不新增构建、设备或发布通过。 |
| C004 | `x` | 证据完成（原记录限定范围） | 独立 workflow、失败日志上传、输入与输出索引、最小权限。<br>**当前：**原任务已勾选；本台账保留该执行范围，不新增构建、设备或发布通过。 |
| C005 | `x` | 证据完成（原记录限定范围） | 准备精确提交及本地重放/推送预览流程；提交 SHA 与提交后的最终重放结果保存在 checkout 外，避免证据自引用。<br>**当前：**原任务已勾选；本台账保留该执行范围，不新增构建、设备或发布通过。 |
| C005a | ` ` | 证据完成 | root 独立审查精确提交对象和最终重放；该项由审查者确认，不由实施自行勾选。<br>**当前：**e4dfa237 / run39842258260，root审查、99文本ZIP逐项复验完成；仅宿主CI，不新造真机证据。E7。 |
| C006 | ` ` | 证据完成 | 用户批准该 SHA 后推送，核对远端 SHA 和对应 Linux CI。<br>**当前：**e4dfa237 / run39842258260，root审查、99文本ZIP逐项复验完成；仅宿主CI，不新造真机证据。E7。 |
| C007 | ` ` | 证据完成 | 下载 artifact、核对服务端 digest/逐文件索引，更新证据；未覆盖项仍待验收。<br>**当前：**e4dfa237 / run39842258260，root审查、99文本ZIP逐项复验完成；仅宿主CI，不新造真机证据。E7。 |

## specs/001-ffmpeg-ohcodec-producer/phase28/tasks.md

来源 S10；本PR基线已跟踪。

| 任务 | 原标记 | 当前分类 | 结论与承接 |
|---|---|---|---|
| T001 | `x` | 证据完成（原记录限定范围） | 核验授权、三仓/12产物、Phase27 snapshot02，保存 out/phase28/authorization.json、boundary-verification.json、phase27-precheck.json。（FR28-01）<br>**当前：**原任务已勾选；本台账保留该执行范围，不新增构建、设备或发布通过。 |
| T002 | `x` | 证据完成（原记录限定范围） | 整合三份 research、官方 callback 文档、当前 Spec Kit 设计与 contracts，保留 out/phase28/service-block-investigation.md。（FR28-02..09）<br>**当前：**原任务已勾选；本台账保留该执行范围，不新增构建、设备或发布通过。 |
| T003 | `x` | 证据完成（原记录限定范围） | 对 spec/plan/contracts/tasks 执行官方 prerequisite 与语义一致性分析，保存 out/phase28/analysis.json；明确实验宏和不可恢复错误边界。（全要求）<br>**当前：**原任务已勾选；本台账保留该执行范围，不新增构建、设备或发布通过。 |
| T004 | `x` | 证据完成（原记录限定范围） | 复制最终 Phase27 源与脚本至 out/phase28/{ffmpeg-input,input-package,build-runtime}，生成 baseline 精确集合锁，禁止复用旧 build。（FR28-01、11）<br>**当前：**原任务已勾选；本台账保留该执行范围，不新增构建、设备或发布通过。 |
| T005 | `x` | 证据完成（原记录限定范围） | [US1] 在 out/phase28/tests/lifecycle/ 提取真实 mapper_uninit/release、vd_lavc reset/uninit、VO control 建立顺序 RED，保存编译成功与语义失败。证据：tests/lifecycle/red-t005-08、RED-BASELINE.json。（FR28-02、03、10）<br>**当前：**原任务已勾选；本台账保留该执行范围，不新增构建、设备或发布通过。 |
| T006 | `x` | 证据完成（原记录限定范围） | [US1] 在 Phase28 mpv 副本实现内部 preflight、同步 VO 清理、Vulkan drain、展示 Surface 不变时旧 Stop/Destroy 先于新 SetSurface；同一 OHCodec consumer 交接仍待绑定验收，正常替帧无全局等待。实现：vd_lavc preflight/EOF延后、vo.c retire、vo_gpu_next capability-gated drain、ohcodec_interop drain；GREEN 见 tests/lifecycle/green-t005-12。（FR28-02、03、04）<br>**当前：**原阶段只证明展示Surface顺序；同consumer的owner/NativeImage/稳定Surface身份由后继Phase30 A02限定验证承接，不能倒推原阶段已证明。 |
| T007 | `x` | 证据完成（原记录限定范围） | [US1] GREEN：无新帧、相同参数复用、旧帧重绘、旧token晚释放、重复drain、异步外部队列与错误返回；所有实际函数依赖绑定。green-t005-26 覆盖同步 drain/历史 external release/旧 token、mapper teardown release-error、owner 查询；设备 vk-switch 覆盖展示 Surface 顺序，未证明同一 consumer 交接；日志标签瑕疵保留说明。（FR28-02、04、08、10）<br>**当前：**原GREEN为函数及展示Surface范围；同consumer交接由Phase30 A02限定正常顺序证据承接，任意并发范围仍未验。 |
| T008 | `x` | 证据完成（原记录限定范围） | [US2] 在 out/phase28/tests/lifecycle/ 建立真实 ohdec 四callback/Close/Flush/token/native-op 的 RED，覆盖在途与同步callback及ctx释放后的晚到调用。证据：tests/lifecycle/red-t008-07、RED-BASELINE.json。（FR28-05、06、10）<br>**当前：**原任务已勾选；本台账保留该执行范围，不新增构建、设备或发布通过。 |
| T009 | `x` | 证据完成（原记录限定范围） | [US2] 在 Phase28 ohdec 副本实现稳定gate、detach/drain、内部helper、token admission，Close内Stop/Destroy、旧token仅留失效壳。GREEN 见 tests/lifecycle/green-t008-08。（FR28-05、06）<br>**当前：**原任务已勾选；本台账保留该执行范围，不新增构建、设备或发布通过。 |
| T010 | `~` | 待验收（部分覆盖） | [US2] GREEN：各初始化失败、重复清理、generation、格式fallback、锁顺序，平台错误失败终局；不以close返回值取消FFmpeg free。已覆盖 Prepare 失败、重复 Close、在途 callback/token、Destroy 失败隔离代码路径；Start/Configure 失败、格式 fallback、平台错误注入真机待补。（FR28-05、06、08、10）<br>**当前：**宿主真实函数和后继正常短场景已覆盖部分；Start/Configure平台失败、格式fallback、所有seek/reinit设备组合无完整证据，保持未验收。 |
| T011 | `x` | 证据完成（原记录限定范围） | [US2] 显式实验宏与独立watchdog真实回归，记录未知GPU完成时不走普通cleanup/fallback，外部有界退出；不将其设为通用mpv默认abort。证据：tests/lifecycle/t011-watchdog-03（normal PASS、experiment -6、missing-abort 变异被拒、external timeout）。（FR28-08）<br>**当前：**原任务已勾选；本台账保留该执行范围，不新增构建、设备或发布通过。 |
| T012 | `~` | 待验收（部分覆盖） | [US3] EOF/new-packet、bootstrap、reinit/fallback、seek入口真实RED后实现deferred reset并GREEN；GL和软件不适用路径无副作用。EOF RED/GREEN 已完成（red-t012-02、green-t005-26）；GL/软件/seek/reinit设备对照待T017。（FR28-07、10）<br>**当前：**宿主真实函数和后继正常短场景已覆盖部分；Start/Configure平台失败、格式fallback、所有seek/reinit设备组合无完整证据，保持未验收。 |
| T013 | `x` | 证据完成（原记录限定范围） | [US3] 从Phase28实际源重跑HDR/SEI/AnnexB/优先级/Python回归，记录源绑定与失败诊断。证据：tests/regression/t013-02、build-runtime 四个 Python 单测全部通过。（FR28-11）<br>**当前：**原任务已勾选；本台账保留该执行范围，不新增构建、设备或发布通过。 |
| T014 | `x` | 证据完成（原记录限定范围） | [US3] 两clean完整/codec-only FFmpeg及mpv构建，原始SHA/ELF/编译链接输入核验，固定原五库/libplacebo，重建本轮准确清单。证据：build/evidence-final.json（FFmpeg e58d1f…、codec-only 57e6a7…、mpv 150f60…、libplacebo 4124ab…；compile inputs passed）。（FR28-09、11）<br>**当前：**原任务已勾选；本台账保留该执行范围，不新增构建、设备或发布通过。 |
| T015 | `x` | 证据完成（原记录限定范围） | [US3] 新独立CI checkout、完整文本输入索引、故障采集门禁、本地干净重放与精确提交预览；新SHA批准后才push。证据：分支 codex/phase28-validation，U1 后提交 52572fe33511f306aef22dd489077446009ddad3（已单独批准）；local-replay-09 passed=true；旧失败 2aea6b1、旧成功 6ca1274/ba586a6 保留。（FR28-11）<br>**当前：**原任务已勾选；本台账保留该执行范围，不新增构建、设备或发布通过。 |
| T016 | `x` | 证据完成（原记录限定范围） | [US3] 新Linux CI与artifact下载全索引/实际workflow/源/dirty状态核验，失败保留，不继承旧绿灯。run 39657429022 success；artifact 12372108316，ZIP SHA256 3db70a41…，135 文件全索引通过；旧失败 run 39635363231/旧成功 39636234441 保留。见 ci/CI-RUN.json。（FR28-11）<br>**当前：**原任务已勾选；本台账保留该执行范围，不新增构建、设备或发布通过。 |
| T017 | `x` | 证据完成（原记录限定范围） | [US3] 新诊断HAP/库/maps/实验宏绑定，deveco-cli构建安装，执行contracts/validation.md设备矩阵及外部watchdog验证。HAP 1a79a08d…，嵌入 libmpv/libavcodec 字节与构建产物核对一致；vk-pq/vk-switch/gl-pq/gl-pq-sw、Close/展示 Surface 顺序、keepScreen=false、独立 hang watchdog 均通过；GPU/Release 设备故障注入仍未验收。（FR28-12）<br>**当前：**GPU/Release有限替换返回码、调用边界停滞与有界退出由后继device-validation/Phase29承接；不等于真实GPU内部调用永久不返，该项仍待验收。 |
| T018 | `x` | 证据完成（原记录限定范围） | [US3] 保屏false读回、空计划、进程停止；最终基线复核、manifest/REPORT/tasks/封存，未验收项目保持pending。keepScreen=false 回显、bm clean -d、force-stop（pidof 空）、REPORT/REVIEW-RESPONSE/tasks 与 seal.json 870f5066…；verify_handoff.py PASS。（FR28-01、12）<br>**当前：**原任务已勾选；本台账保留该执行范围，不新增构建、设备或发布通过。 |
| T019 | `x` | 证据完成（原记录限定范围） | [US2/US3] 独立审查 F1–F5、复审 R1–R3 与 U1 返修：Surface terminal 状态与拒绝新 producer、Stop/Destroy 有界终局、empty-current 历史 external release 等待、generic teardown 锁存、持久 owner 查询、watchdog 变异门禁、交接/seal 非循环一致性。U1 后 CI run 39657429022 success；证据 REVIEW-RESPONSE.md、green-t005-26、red-t005-12、t011-watchdog-06、verify_handoff.py。（FR28-08、10、11）<br>**当前：**此处U1外层retained仍不足以覆盖完整父级释放链，已由device-validation D012–D014真实父链/终止屏障与负例取代；普通产品UNSAFE策略再由Phase29及Player004显式接管承接。 |

## specs/001-ffmpeg-ohcodec-producer/phase31-normal-validation/tasks.md

来源 S11；本PR基线已跟踪。

| 任务 | 原标记 | 当前分类 | 结论与承接 |
|---|---|---|---|
| N001 | `x` | 证据完成（原记录限定范围） | FR01/02/10 冻结边界、正常库身份、凭据可用性与设备连接。<br>**当前：**原任务已勾选；本台账保留该执行范围，不新增构建、设备或发布通过。 |
| N002 | `x` | 证据完成（原记录限定范围） | FR01-10/SC01-04 Spec Kit prerequisites与root语义审查。<br>**当前：**原任务已勾选；本台账保留该执行范围，不新增构建、设备或发布通过。 |
| N003 | `x` | 证据完成（原记录限定范围） | FR04-09 真实操作控制与证据门禁RED/边界/失败，最小实现GREEN。<br>**当前：**原任务已勾选；本台账保留该执行范围，不新增构建、设备或发布通过。 |
| N004 | `x` | 证据完成（原记录限定范围） | FR01 正常独立HAP构建，源码/编译输入/9库/7映射身份。<br>**当前：**原任务已勾选；本台账保留该执行范围，不新增构建、设备或发布通过。 |
| N005 | `x` | 证据完成（原记录限定范围） | FR04-08 本地/短NAS操作场景，正常Ability关闭重开与清理后外部冷重开分列，实际事件与清理验证。<br>**当前：**原任务已勾选；本台账保留该执行范围，不新增构建、设备或发布通过。 |
| N006 | ` ` | 替代或范围调整 | FR02/03/SC03 单独60min NAS长播、时间线/资源/凭据清理证据。<br>**当前：**长播01连续788.048305秒后进入后台，历史FAIL保留；取消60分钟前置，不再要求本轮重测或追查原因，不改为PASS。 |
| N007 | ` ` | 证据完成 | FR09/10 root独立审查、失败保留、持久封存与保护边界。<br>**当前：**427148d8 / run39961210476，87项宿主检查、17索引文本及root审查完成；原封存的待CI字段为历史状态。E10。 |
| N008 | ` ` | 证据完成 | FR10 纯文本CI包、精确clean本地重放与本地SHA预览，不推送。<br>**当前：**427148d8 / run39961210476，87项宿主检查、17索引文本及root审查完成；原封存的待CI字段为历史状态。E10。 |

## tools/phase29-normal-terminal/spec/tasks.md

来源 S12；本PR基线已跟踪。

| 任务 | 原标记 | 当前分类 | 结论与承接 |
|---|---|---|---|
| I001 | `x` | 证据完成（原记录限定范围） | 核验464文件封存，建立独立规格与保护边界。<br>**当前：**原任务已勾选；本台账保留该执行范围，不新增构建、设备或发布通过。 |
| I002 | `x` | 证据完成（原记录限定范围） | ABI先RED后GREEN、大小/version/线程契约、C/C++实际动态链接。<br>**当前：**原任务已勾选；本台账保留该执行范围，不新增构建、设备或发布通过。 |
| I003 | `x` | 证据完成（原记录限定范围） | 锁定SDK/依赖，normal-e/f clean同字节，旧54+4接口，目标C/C++强引用链接。<br>**当前：**原任务已勾选；本台账保留该执行范围，不新增构建、设备或发布通过。 |
| I004 | `x` | 证据完成（原记录限定范围） | logger阻塞真实RED后改独立deadline；真实ArkTS保屏竞态和UI投递RED/GREEN。<br>**当前：**原任务已勾选；本台账保留该执行范围，不新增构建、设备或发布通过。 |
| I005 | `x` | 证据完成（原记录限定范围） | 独立app真机双次真实播放、无注册禁止fallback、SAFE_RELEASE_ERROR拒绝新producer但不误退出、UI故障提示/保屏回读/主动终止、callback/UI/logger阻塞deadline。<br>**当前：**原任务已勾选；本台账保留该执行范围，不新增构建、设备或发布通过。 |
| I006 | ` ` | 证据完成 | root最终精确提交审查及推送预览；提交后本地精确重放。未批准推送，远端Linux CI待验。<br>**当前：**6520a29a / run39855543387，118文本ZIP核验、root审查完成；异常结束不等于常规资源清理。E8。 |

## tools/phase30-consumer-handoff/spec/tasks.md

来源 S13；本PR基线已跟踪。

| 任务 | 原标记 | 当前分类 | 结论与承接 |
|---|---|---|---|
| C001 | `x` | 证据完成（原记录限定范围） | 校验旧封存、保护边界与源码；旧应用四项历史输入未独立封存已如实报告。<br>**当前：**原任务已勾选；本台账保留该执行范围，不新增构建、设备或发布通过。 |
| C002 | `x` | 证据完成（原记录限定范围） | Spec Kit prerequisites（NO_PERSIST）及 root 规格分析通过。<br>**当前：**原任务已勾选；本台账保留该执行范围，不新增构建、设备或发布通过。 |
| C003 | `x` | 证据完成（原记录限定范围） | 观测/解析 RED、真实 FFmpeg 同步回归、去 Close 等待变异拒绝；A/B 解析夹具各 16 项。<br>**当前：**原任务已勾选；本台账保留该执行范围，不新增构建、设备或发布通过。 |
| C004 | `x` | 证据完成（原记录限定范围） | 独立 TRACE/TEST 仪表与应用双请求线程；normal 终局策略保持。<br>**当前：**原任务已勾选；本台账保留该执行范围，不新增构建、设备或发布通过。 |
| C005 | `x` | 证据完成（原记录限定范围） | 目标构建及 A02/B03 真机，实际源快照、编译器依赖、HAP 与映射身份绑定。<br>**当前：**原任务已勾选；本台账保留该执行范围，不新增构建、设备或发布通过。 |
| C006a | `x` | 证据完成 | root 原始设备/来源/清理独立复核。<br>**当前：**b29ef3a1 / run39923292047，51文件ZIP核验、root审查完成；A02/B03限定范围不扩大。E9。 |
| C006b | ` ` | 证据完成 | 新 CI 文本包本地精确提交重放、最终边界、精确推送预览。<br>**当前：**b29ef3a1 / run39923292047，51文件ZIP核验、root审查完成；A02/B03限定范围不扩大。E9。 |
| C007 | ` ` | 证据完成 | 用户批准新 SHA 后才推送并运行 Ubuntu CI；本地 macOS 通过不可替代。<br>**当前：**b29ef3a1 / run39923292047，51文件ZIP核验、root审查完成；A02/B03限定范围不扩大。E9。 |

共覆盖 13 份任务文件、172 项任务；每项均有分类。
