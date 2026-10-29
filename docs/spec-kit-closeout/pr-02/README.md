# PR2：精确依赖输入与运行目录规格收尾

父提交：`ad0e403e4f7a3fb4d39bbb4c963d0d1994dad080`。本基线**没有specs目录中的Phase18/19/20规格**；实现位于tools/phase18、tools/phase20，原始规格实际位于producer原工作区specs/001-ffmpeg-ohcodec-producer/phase18、phase19、phase20。本轮逐任务登记并固定摘要，未伪称这些原件已经包含在PR中。

## 旧新规格映射与核对结论

| 历史项 | 当前结论 | 证据与承接 |
|---|---|---|
| Phase17复用静态依赖缺口 → Phase18 T001–017/20–22 | 已在独立新根从精确源码重建十项依赖并核对功能、来源/工具/许可证/绑定；不补造历史缓存事件 | E1；[固定Phase18工具与输入](https://github.com/yaoshining/ohos_ijkplayer/tree/ad0e403e4f7a3fb4d39bbb4c963d0d1994dad080/tools/phase18) |
| Phase18 T018/T019原“待批准/CI未执行” → Phase19 T001–010 | 后续已获精确批准，最终CI2d65a50b及下载复验完成；原1d5227c4封存不改写 | E2；[run39156616632](https://github.com/yaoshining/ohos_ijkplayer/actions/runs/39156616632)，head2d65a50b3a4c3d09fdb925bcb92a2af307a1a704；2689项artifact核验 |
| Phase9运行目录提案 → Phase20 T001–014 | 进程不可变配置、冲突/重入、真实Samba入口、双fresh目标构建与下载复验完成 | E3–E5；[固定runtime实现](https://github.com/yaoshining/ohos_ijkplayer/tree/ad0e403e4f7a3fb4d39bbb4c963d0d1994dad080/tools/phase20/runtime)，[native run39217268165](https://github.com/yaoshining/ohos_ijkplayer/actions/runs/39217268165)、[target run39218428737](https://github.com/yaoshining/ohos_ijkplayer/actions/runs/39218428737) |
| Phase20“Player调用/资源/设备未接入” | 后续独立应用由PR3 Phase21–31验证，实际Player最小接入由PR4的004承接 | 不把Phase20自身改成设备通过；TV最终接入/正式替换仍未授权 |

约254MB固定源码/SDK输入属于本PR既有范围，本轮不添加或更改二进制。新来源闭包通过不证明历史缓存事件或预构建工具链自举来源。Python目标目录修复保留，实际资源与运行目录交付由调用方负责，目录字符串存在不等于设备可用。

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

该交付基线不含完整`.specify`工具入口，未伪称已在本分支运行官方prerequisite；本轮只读逐份任务、相关规格说明和实际证据，文档覆盖与摘要校验另记。 本轮仅文档，无功能开发，不新建或重跑功能TDD。旧TDD时序/失败照原证据保留。
