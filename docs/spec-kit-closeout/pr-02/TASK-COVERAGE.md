# 任务逐项覆盖台账

核对日2026-10-24。以原任务ID为键；“证据完成”仅指该行已记录的范围。旧任务文件不改写。局部任务以限定说明为准，不能把本表当正式验收全通过。

## specs/001-ffmpeg-ohcodec-producer/phase18/tasks.md

来源 S1；**未在此PR基线跟踪**，本轮仅登记本机实际规格与摘要，不能当作公开原件。

| 任务 | 原标记 | 当前分类 | 结论与承接 |
|---|---|---|---|
| T001 | `x` | 证据完成（原记录限定范围） | 在 out/phase18/precheck.json 重验旧封存、TV与Player新起点（FR-001）。<br>**当前：**原任务已勾选；本台账保留该执行范围，不新增构建、设备或发布通过。 |
| T002 | `x` | 证据完成（原记录限定范围） | 在 specs/001-ffmpeg-ohcodec-producer/phase18 完成spec/plan/研究/数据模型/快速指南并实际运行setup脚本。<br>**当前：**原任务已勾选；本台账保留该执行范围，不新增构建、设备或发布通过。 |
| T003 | `x` | 证据完成（原记录限定范围） | 只读analyze规格、计划、任务并执行prerequisite，结果输出至会话（FR-006/010）。<br>**当前：**原任务已勾选；本台账保留该执行范围，不新增构建、设备或发布通过。 |
| T004 | `x` | 证据完成（原记录限定范围） | 在 out/phase18/tests/test_inputs.py 写源码完整集/摘要/逃逸/target对象/新运行根与Git版本标记正常边界失败回归并保存RED。<br>**当前：**原任务已勾选；本台账保留该执行范围，不新增构建、设备或发布通过。 |
| T005 | `x` | 证据完成（原记录限定范围） | 在 out/phase18/runtime/input_gate.py 最小实现输入与运行根门禁，保存GREEN（FR-004/006）。<br>**当前：**原任务已勾选；本台账保留该执行范围，不新增构建、设备或发布通过。 |
| T006 | `x` | 证据完成（原记录限定范围） | 在 out/phase18/locks 锁实际Python模块/编译器/生成器/SDK/std与工具动态依赖（FR-003）。<br>**当前：**原任务已勾选；本台账保留该执行范围，不新增构建、设备或发布通过。 |
| T007 | `x` | 证据完成（原记录限定范围） | [US1] 在 out/phase18/source-package 导出精确Git/Lua/84crates，记录原始archive/patch、校验完整集（FR-002/004）。<br>**当前：**原任务已勾选；本台账保留该执行范围，不新增构建、设备或发布通过。 |
| T008 | `x` | 证据完成（原记录限定范围） | [US1] 在 out/phase18/tests/test_recipes.py 先写版本边界、HB/FT能力、prefix/DESTDIR、Lua flags与offline回归，保存RED（FR-006）。<br>**当前：**原任务已勾选；本台账保留该执行范围，不新增构建、设备或发布通过。 |
| T009 | `x` | 证据完成（原记录限定范围） | [US1] 在 out/phase18/runtime/build_deps.py 实现新根、隔离env与八库顺序，稳定prefix/pc，保存GREEN及真实编译安装日志（FR-002/004/005）。<br>**当前：**原任务已勾选；本台账保留该执行范围，不新增构建、设备或发布通过。 |
| T010 | `x` | 证据完成（原记录限定范围） | [US1] 在 out/phase18/runtime/build_shaderc.py 实现四repo必要生成器与combined构建，最小patch先RED/GREEN（FR-002/005/006）。<br>**当前：**原任务已勾选；本台账保留该执行范围，不新增构建、设备或发布通过。 |
| T011 | `x` | 证据完成（原记录限定范围） | [US1] 在 out/phase18/runtime/build_dovi.py 实现完整offline vendor与新target/staticlib/header构建，保留日志（FR-002/004/005）。<br>**当前：**原任务已勾选；本台账保留该执行范围，不新增构建、设备或发布通过。 |
| T012 | `x` | 证据完成（原记录限定范围） | [US1] 在 out/phase18/runtime/collect_dependencies.py 绑定实际编译命令/头/生成规则/对象/同名archive occurrence/安装文件；测试拒绝无来源target输入（FR-005/006）。<br>**当前：**原任务已勾选；本台账保留该执行范围，不新增构建、设备或发布通过。 |
| T013 | `x` | 证据完成（原记录限定范围） | [US1] 在 out/phase18/licenses 和 out/phase18/sbom.json 收集所有实际组件/工具边界许可与来源（FR-005/010）。<br>**当前：**原任务已勾选；本台账保留该执行范围，不新增构建、设备或发布通过。 |
| T014 | `x` | 证据完成（原记录限定范围） | [US2] 在 out/phase18/native-tests 对相关组件执行有效宿主功能测试，锁测试输入，不接受零测试（FR-008）。<br>**当前：**原任务已勾选；本台账保留该执行范围，不新增构建、设备或发布通过。 |
| T015 | `x` | 证据完成（原记录限定范围） | [US2] 在 out/phase18/integration/input-package 生成新依赖包并绑定source/build/install（FR-007）。<br>**当前：**原任务已勾选；本台账保留该执行范围，不新增构建、设备或发布通过。 |
| T016 | `x` | 证据完成（原记录限定范围） | [US2] 在 out/phase18/integration/runtime 复制并适配Phase17构建/输入收集/契约门禁，改动先RED/GREEN（FR-006/007）。<br>**当前：**原任务已勾选；本台账保留该执行范围，不新增构建、设备或发布通过。 |
| T017 | `x` | 证据完成（原记录限定范围） | [US2] 在 out/phase18/integration/runs 两个新绝对根构建LP/mpv，验证139宏/54API/247import/bridge/OHCodec/GL/Vulkan注册调用及实际新库输入，报告配置与字节差异（FR-007/008）。<br>**当前：**原任务已勾选；本台账保留该执行范围，不新增构建、设备或发布通过。 |
| T018 | ` ` | 证据完成 | [US3] 在 out/phase18/ci/checkout 实现新源码十库+LP/mpv工作流与实际Linux工具输入锁、CI契约回归（FR-003/006/009）。<br>**当前：**Phase19承接CI；2d65a50b / run39156616632成功、2689项下载复验。原Phase18待批准记录不改。E2。 |
| T019 | ` ` | 证据完成 | [US3] 仅推送独立诊断分支，运行新CI，将结果/下载/校验记录到 out/phase18/ci（FR-009）。<br>**当前：**Phase19承接CI；2d65a50b / run39156616632成功、2689项下载复验。原Phase18待批准记录不改。E2。 |
| T020 | `x` | 证据完成（原记录限定范围） | [US3] 在 out/phase18/final-boundary.json 重验旧证据及本轮产品/HEAD/index起点（FR-001）。<br>**当前：**原任务已勾选；本台账保留该执行范围，不新增构建、设备或发布通过。 |
| T021 | `x` | 证据完成（原记录限定范围） | [US3] 在 docs/producer-phase18-report.md 与 out/phase18/manifest.json、handoff.json 分别报告新来源闭包/旧unknown/设备pending和formal=false（FR-010）。<br>**当前：**原任务已勾选；本台账保留该执行范围，不新增构建、设备或发布通过。 |
| T022 | `x` | 证据完成（原记录限定范围） | 将全部新文件与独立CI发布内容绑定 out/phase18/evidence-index.json、seal.json，重新回读（FR-010）。<br>**当前：**原任务已勾选；本台账保留该执行范围，不新增构建、设备或发布通过。 |

## specs/001-ffmpeg-ohcodec-producer/phase19/tasks.md

来源 S2；**未在此PR基线跟踪**，本轮仅登记本机实际规格与摘要，不能当作公开原件。

| 任务 | 原标记 | 当前分类 | 结论与承接 |
|---|---|---|---|
| T001 | `x` | 证据完成（原记录限定范围） | [US1] 在 out/phase19/approval.json 记录已查证的人类批准（FR-002）。<br>**当前：**原任务已勾选；本台账保留该执行范围，不新增构建、设备或发布通过。 |
| T002 | `x` | 证据完成（原记录限定范围） | [US1] 在 out/phase19/tests/test_approval_gate.py 先RED，再 approval_gate.py 实现/GREEN（FR-002/004）。该批准保护测试实际先于本tasks最终落盘，不追认完整SpecKit先后。<br>**当前：**原任务已勾选；本台账保留该执行范围，不新增构建、设备或发布通过。 |
| T003 | `x` | 证据完成（原记录限定范围） | [US1] 在 out/phase19/precheck.json 与 product-boundary-start.json 复验旧135126项和业务边界（FR-001）。<br>**当前：**原任务已勾选；本台账保留该执行范围，不新增构建、设备或发布通过。 |
| T004 | `x` | 证据完成（原记录限定范围） | 完成 Phase19 spec/plan/research/data-model/quickstart/tasks，实际setup及analyze。<br>**当前：**原任务已勾选；本台账保留该执行范围，不新增构建、设备或发布通过。 |
| T005 | `x` | 证据完成（原记录限定范围） | [US1] 创建 out/phase19/ci/checkout，复核原提交并推送已批准诊断分支（FR-002/003）。<br>**当前：**原任务已勾选；本台账保留该执行范围，不新增构建、设备或发布通过。 |
| T006 | `x` | 证据完成（原记录限定范围） | [US2] 在 out/phase19/attempts 保存真实CI运行、失败及回归RED/GREEN；最小脚本修复与内容预览分别记录（FR-003/004）。<br>**当前：**原任务已勾选；本台账保留该执行范围，不新增构建、设备或发布通过。 |
| T007 | `x` | 证据完成（原记录限定范围） | [US2] 在诊断工作流记录apt/pip/runner身份与实际构建前工具、SDK输入（FR-005）。<br>**当前：**原任务已勾选；本台账保留该执行范围，不新增构建、设备或发布通过。 |
| T008 | `x` | 证据完成（原记录限定范围） | [US3] 下载新CI artifact并校验ZIP、文件全集、实际新十库、139宏/54API/247imports/OHCodec和双目录一致（FR-006）。<br>**当前：**原任务已勾选；本台账保留该执行范围，不新增构建、设备或发布通过。 |
| T009 | `x` | 证据完成（原记录限定范围） | [US3] 更新 docs/producer-phase19-report.md、manifest/handoff及最终只读边界（FR-001/007）。<br>**当前：**原任务已勾选；本台账保留该执行范围，不新增构建、设备或发布通过。 |
| T010 | `x` | 证据完成（原记录限定范围） | [US3] 封存 out/phase19/evidence-index.json 和 seal.json 并回读（FR-007）。<br>**当前：**原任务已勾选；本台账保留该执行范围，不新增构建、设备或发布通过。 |

## specs/001-ffmpeg-ohcodec-producer/phase20/tasks.md

来源 S3；**未在此PR基线跟踪**，本轮仅登记本机实际规格与摘要，不能当作公开原件。

| 任务 | 原标记 | 当前分类 | 结论与承接 |
|---|---|---|---|
| T001 | `x` | 证据完成（原记录限定范围） | 核实人类授权与Phase19全索引，记录out/phase20/authorization-and-precheck.json。<br>**当前：**原任务已勾选；本台账保留该执行范围，不新增构建、设备或发布通过。 |
| T002 | `x` | 证据完成（原记录限定范围） | 创建独立clone、规格和计划，运行官方setup脚本并保持feature指针不变。<br>**当前：**原任务已勾选；本台账保留该执行范围，不新增构建、设备或发布通过。 |
| T003 | `x` | 证据完成（原记录限定范围） | [P] 在out/phase20/research完成Samba映射及mpv/fontconfig边界研究，固化contracts/runtime.md。<br>**当前：**原任务已勾选；本台账保留该执行范围，不新增构建、设备或发布通过。 |
| T004 | `x` | 证据完成（原记录限定范围） | 运行官方prerequisite并阅读spec/plan/tasks完成out/phase20/analysis.md，检查全部需求覆盖。<br>**当前：**原任务已勾选；本台账保留该执行范围，不新增构建、设备或发布通过。 |
| T005 | `x` | 证据完成（原记录限定范围） | [US1] 在clone/tools/phase20/tests编写并运行配置/path/分配/幂等/冲突回归，保存out/phase20/tests RED。<br>**当前：**原任务已勾选；本台账保留该执行范围，不新增构建、设备或发布通过。 |
| T006 | `x` | 证据完成（原记录限定范围） | [US1] 实现clone/tools/phase20/runtime进程级不可变配置和真实锁，通过GREEN。<br>**当前：**原任务已勾选；本台账保留该执行范围，不新增构建、设备或发布通过。 |
| T007 | `x` | 证据完成（原记录限定范围） | [US2] 为clone/tools/phase20/apply.py的源码补丁与实际new/init/free/legacy入口编写失败回归。<br>**当前：**原任务已勾选；本台账保留该执行范围，不新增构建、设备或发布通过。 |
| T008 | `x` | 证据完成（原记录限定范围） | [US2] 实现Samba显式加载、目录覆盖、HOME缓存回退阻断、完整对象计数、重入拒绝和FFmpeg包装；验证交错/失败/重复初始化。<br>**当前：**原任务已勾选；本台账保留该执行范围，不新增构建、设备或发布通过。 |
| T009 | `x` | 证据完成（原记录限定范围） | [US3] 创建clone/tools/phase20/build.py、锁实际工具/输入并完成out/phase20/local-v3的两次全新目标构建（v1/v2失败范围保留）。<br>**当前：**原任务已勾选；本台账保留该执行范围，不新增构建、设备或发布通过。 |
| T010 | `x` | 证据完成（原记录限定范围） | [US3] 检查新导出/旧ABI/对象与静态链接来源、Python路径和默认生成器，保留差异及日志。<br>**当前：**原任务已勾选；本台账保留该执行范围，不新增构建、设备或发布通过。 |
| T011 | `x` | 证据完成（原记录限定范围） | [US3] 准备精确发布预览，复用批准SDK/源码与工作流执行实际CI，保存out/phase20/attempts。<br>**当前：**原任务已勾选；本台账保留该执行范围，不新增构建、设备或发布通过。 |
| T012 | `x` | 证据完成（原记录限定范围） | [US3] 下载实际artifact并独立核验ZIP、文件全集和目标二进制/绑定。<br>**当前：**原任务已勾选；本台账保留该执行范围，不新增构建、设备或发布通过。 |
| T013 | `x` | 证据完成（原记录限定范围） | 复验旧证据/三仓边界，写docs/producer-phase20-report.md和out/phase20/manifest.json、handoff.json。<br>**当前：**原任务已勾选；本台账保留该执行范围，不新增构建、设备或发布通过。 |
| T014 | `x` | 证据完成（原记录限定范围） | 封存out/phase20/evidence-index.json、seal.json并再次回读。<br>**当前：**原任务已勾选；本台账保留该执行范围，不新增构建、设备或发布通过。 |

共覆盖 3 份任务文件、46 项任务；每项均有分类。
