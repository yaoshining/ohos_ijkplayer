# PR1：构建与来源规格收尾

父提交：`67d35542db274c0dd5f45fb3c2be4ea02dc734c2`。只在新增目录追加四个文档文件。

## 旧新规格映射与核对结论

| 历史项 | 当前结论 | 后继/证据入口 |
|---|---|---|
| 总tasks T705–T707（Phase8） | 本机两fresh与CI下载实物、差异/冻结报告已完成；旧未勾选属于回填缺口 | E1/E2；[1f053ecd固定实现](https://github.com/yaoshining/ohos_ijkplayer/tree/1f053ecd4677cef1006418e08504e48f39cc2770/tools/ffmpeg8)，[run39064232170](https://github.com/yaoshining/ohos_ijkplayer/actions/runs/39064232170)；首轮39063582339失败保留 |
| Phase9历史来源与运行目录提案 | 调查完成不等于历史安装身份闭合；目录提案由PR2 Phase20、PR4初始化承接 | Phase9本机规格未在本基线跟踪，摘要与任务已登记；不能声称本PR已发布原件 |
| Phase10 HX509 T006–009/T014–019 | resume-01普通兼容与分析范围完成；静态111项相同，配对六库不等、固定静态根相等 | E3/E4；[run39111716645](https://github.com/yaoshining/ohos_ijkplayer/actions/runs/39111716645)，6b2790ad5aaf5b9f67c2a52b852b6202013aacbe；历史失败39108567338不改 |
| Phase10 T010/T011 | parser/lexer故障注入及sanitizer仍未完成/暂停 | 保持待验收，其他阶段sanitizer不能替代 |
| Phase10 T012、Phase11/12来源调查 | 跨目录配对重复性由Phase11完成；精确历史lexer安装身份未证明；停止以旧哈希全等为目标 | [Phase11报告](https://github.com/yaoshining/ohos_ijkplayer/blob/67d35542db274c0dd5f45fb3c2be4ea02dc734c2/docs/producer-phase11-report.md)、[Phase12报告](https://github.com/yaoshining/ohos_ijkplayer/blob/67d35542db274c0dd5f45fb3c2be4ea02dc734c2/docs/producer-phase12-report.md)；Phase11 run39124039398 |
| Phase13–16功能完整性与互操作恢复 | 本机规格记录独立调查/恢复，不追认旧来源；后继Phase17验证、Phase18新源码闭包 | 这些本机spec未入本基线；当前任务登记不等于迁移全部原件 |
| Phase17 T001–009 | 同平台两fresh、输入/宏比较与CI已完成；历史复用静态依赖缺口仍在当时报告保留 | E5–E7；[Phase17入口](https://github.com/yaoshining/ohos_ijkplayer/blob/67d35542db274c0dd5f45fb3c2be4ea02dc734c2/tools/phase17/README.md)，[run39145167893](https://github.com/yaoshining/ohos_ijkplayer/actions/runs/39145167893)；335项下载复验 |

Phase17本机与Linux各内部两次SHA一致，不声称跨工具链字节一致。139宏/1366输入相符不是物理播放验收。历史静态来源缺口由PR2选择新精确源码重建，不能倒推旧缓存来源已知。默认生成器保持不变；HX509是独立诊断配置。

## 范围与当前规则

本台账依据2026-10-24用户授权做纯文档收尾，追加解释旧记录，不覆盖旧 spec/plan/tasks、seal、索引、报告或代码。`formalArtifactAllowed=false`；TV、原Player工作树、旧候选/HAR/default SDK均不改。不构建、不连接设备、不改系统设置、不重跑长播，不提交未来实现通过结论。四PR是交付拆分而不是四个额外功能。

当前规则按后续明确人类决定覆盖历史时点表述：保留Python目标目录修复；不再追求TV旧二进制全哈希一致；60分钟NAS长播不作为最小接入/PR前置，旧FAIL仍为FAIL，不拼接时长、不归因用户操作。应用仅使用保屏。正常UNSAFE允许提示后受控结束应用，后续Player显式接管；这不是可恢复播放或普通退出清理承诺。

“证据完成”表示列明的宿主/目标/设备子范围完成，“替代或范围调整”不等于原项通过，“待验收”保留测试边界，“证据不足待核对”不猜测结论。已勾选旧项仅沿用其原记录范围，不表示本轮重新执行。

## 四PR对应关系

| PR | 职责与固定基线 | 对应收尾位置 |
|---|---|---|
| 1 | 构建闭包、Spec Kit、宿主工具锁、跨目录重复性；`67d35542db274c0dd5f45fb3c2be4ea02dc734c2` | 本仓 docs/spec-kit-closeout/pr-01；目标docs分支 codex/docs-pr1-speckit-closeout，尚待审查/推送 |
| 2 | 精确输入和静态依赖闭包、Samba运行目录；`ad0e403e4f7a3fb4d39bbb4c963d0d1994dad080` | 本仓 docs/spec-kit-closeout/pr-02；目标docs分支 codex/docs-pr2-speckit-closeout，尚待审查/推送 |
| 3 | OHCodec/HDR/父级释放链/正常terminal及运行验证；`427148d8b52f7dfa920e7ebd05fd8f2f8c6b135b` | 本仓 docs/spec-kit-closeout/pr-03；目标docs分支 codex/docs-pr3-speckit-closeout，尚待审查/推送 |
| 4 | Player正常核心输入、初始化、终局接管、最小消费 | [Player固定提交66e9d335](https://github.com/yaoshining/VidAll_Player/tree/66e9d3350bc64f41d26cb1938fa94027a1642b65/specs/004-normal-core-integration)；Player文档收尾另分支 |

其他PR的收尾路径是**未来目标**，本分支未包含时不提供伪本地链接。PR1与PR2是独立链，PR3累计PR2；合并组合尚未验证，旧CI不得归给新组合。不要按Phase再拆重复PR。

## 尚未闭合的交付门禁

部分阶段工作流只监听特定分支push，尚未为计划PR/组合合并补齐等价门禁；build-ffmpeg8虽有pull_request也不能替代各阶段。此项是后续单独代码/CI工作，本轮不改工作流。新文档SHA须经过精确预览和批准才推送；本台账列举历史run，不声称当前文档提交已经有新CI。

公开证据入口固定到下列Git SHA和Actions run。本机原件位置/摘要见[EVIDENCE](EVIDENCE.md)及[SOURCE-INVENTORY](SOURCE-INVENTORY.json)，不把仅本机原件说成已入库或公开闭环；本轮没有重新下载历史artifact。逐任务覆盖见[TASK-COVERAGE](TASK-COVERAGE.md)。

## 本轮文档分析记录

官方prerequisite默认调用因基线不含`.specify/feature.json`而无法选中feature；随后以只读`SPECIFY_FEATURE_DIRECTORY=specs/001-ffmpeg-ohcodec-producer`及`SPECIFY_FEATURE_NO_PERSIST=1`运行`--json --require-tasks --include-tasks`成功。未创建或修改选择器。 本轮仅文档，无功能开发，不新建或重跑功能TDD。旧TDD时序/失败照原证据保留。
