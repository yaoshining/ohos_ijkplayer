# PR3：运行与生命周期规格收尾

> 最终状态更新（2026-10-29）：合并、默认分支 CI 和仍待验收范围见[最终收尾索引](../../../specs/CLOSEOUT-20261029.md)。下文保留历史时点原文；早期“未推送／未合并／待 CI”不再代表已完成过程的当前状态，旧失败和未验证项不改写。

父提交：`427148d8b52f7dfa920e7ebd05fd8f2f8c6b135b`。分支名phase28但已累计到Phase31；不按每个阶段重复提交。

## 旧新规格映射与核对结论

| 历史项 | 当前结论 / 后继 |
|---|---|
| Phase21初始化集成、Phase22初次设备 | 初期SMB/默认GL/资源增长失败保留；具体失败由Phase23–28分别处理，不能把所有Phase22项批量转PASS。Phase22最终CI由snapshots/03（E11）补齐，12项宿主测试、56文件核验，未重跑设备 |
| Phase23 T019/T020 | E1/E2证明CI3e7e9e34、108项artifact核验与清理完成；SMB最低方言是夹具问题，不声称重建库修复SMB |
| Phase24 T010/16/17/18 | 指定NAS尝试和HDR分层记录保留；CI已完成。HDR库问题转Phase27，Vulkan释放转Phase28；长播未通过仍FAIL，取消前置要求 |
| Phase25/26采样/窗口焦点、HDR诊断 | 记录能力及宿主CI完成；原PQ硬解MDM/CLL缺失为确认失败，Phase27修复；不继续以查明后台切换来源为接入前置 |
| Phase27 HDR亮度元数据与同PQ缓存 | 宿主、双构建及限定设备路径已完成；Vulkan释放诊断承接Phase28。物理HDR/实际亮度不由metadata日志代替 |
| Phase28 T010/T012 | 宿主及后续正常seek/reinit部分覆盖；Start/Configure平台失败、格式fallback全部设备矩阵仍待验收 |
| Phase28父级retained链、device-validation D012–014 | 完整父链与诊断屏障已有真实函数RED/GREEN/负例及限定设备证据；旧U1仅mapper保留不足的失败不删除。父级链CI C005a/C006/C007已完成（E7） |
| Phase28旧“normal真实UNSAFE策略未启用” → Phase29 | 已由normal公共ABI、显式注册、有界deadline与独立app接管承接；I006审查/精确重放/CI完成（E8）。不再把产品处理方案本身列为未实现 |
| Phase29 → Phase30 A02 | TRACE-only正常构建，TEST/DIAGNOSTIC关闭；同owner/NativeImage/consumer Surface的4代decoder、3次顺序交接已证 |
| Phase30 B03 | 单mpv实例TRACE+TEST受控真实线程交错已证；callback获admit、Close等待active，两个不同TID请求阻塞core dispatch，旧Destroy先于新SetSurface。实际2代decoder，seek=-12是拒绝，不是成功并发seek；任意多实例/极端并发仍待验 |
| Phase30 C006/C007 | 精确b29ef3a1、LinuxCI与51文件artifact/root复核完成（E9），旧CURRENT待批准不回写 |
| Phase31 N005/N006 | 七短场景通过，含成功seek、切片、暂停恢复、前后台与关闭重开限定范围。一次SDR现场声音口型观察已确认；长播01仅788.048305秒，历史FAIL保留。60分钟不再是前置，无需为收尾重跑或解释后台触发原因 |
| Phase31 N007/N008 | 审查/封存/精确clean重放/CI已完成（E10）；87宿主检查不等于新设备运行 |
| producer独立app → Player004 | PR4已完成最小消费及47宿主CI检查，原TV不变。Phase29独立app已分别验证host kill/native86，不能跨应用继承：Player004终局接缝仍未独立区分host kill和native deadline实际退出机制 |

## 固定CI索引（历史精确SHA，不归给本次文档SHA）

| 阶段 | 精确提交 | Actions run | 已核验范围 |
|---|---|---|---|
| 22 | 4ad9c4ceaf7491c868d9dd30d8631df6f4352c46 | [39366120567](https://github.com/yaoshining/ohos_ijkplayer/actions/runs/39366120567) | E11，56项文本，12宿主测试 |
| 23 | 3e7e9e3451fc9af38f42d0a16a8c097331848b4d | [39373185636](https://github.com/yaoshining/ohos_ijkplayer/actions/runs/39373185636) | E1，108项文本，非目标执行 |
| 24 | 6fe31c944edd82b5faafb093bae9336cc40a2e11 | [39418975083](https://github.com/yaoshining/ohos_ijkplayer/actions/runs/39418975083) | E3，207项，长播/HDR完整false |
| 26 | 3f4dd429f8c41f1623165eed92548b1f13b5b660 | [39481375467](https://github.com/yaoshining/ohos_ijkplayer/actions/runs/39481375467) | E4，39项；首次遗漏隐藏workflow失败保留 |
| 27 | 341afc67b09f47c1ba9a195a4011e2a7b7eb83f3 | [39580473609](https://github.com/yaoshining/ohos_ijkplayer/actions/runs/39580473609) | E5，修复后成功；旧b9f7失败保留 |
| 28 U1 | 52572fe33511f306aef22dd489077446009ddad3 | [39657429022](https://github.com/yaoshining/ohos_ijkplayer/actions/runs/39657429022) | [旧快照](https://github.com/yaoshining/ohos_ijkplayer/tree/427148d8b52f7dfa920e7ebd05fd8f2f8c6b135b/docs/phase28/validation-snapshot)，不代表父级链修复已包含 |
| 28完整父链 | e4dfa2370d6acea454f1ce2e802f11991a2880b7 | [39842258260](https://github.com/yaoshining/ohos_ijkplayer/actions/runs/39842258260) | E7，99文本；RED5/GREEN12及真实负例 |
| 29 | 6520a29a83dc59f0bec57bf35684ba6f79c2fb43 | [39855543387](https://github.com/yaoshining/ohos_ijkplayer/actions/runs/39855543387) | E8，118文本；normal ABI/父链/真实阻塞deadline |
| 30 | b29ef3a1a5b2b42488324af7ac3591b55df2779d | [39923292047](https://github.com/yaoshining/ohos_ijkplayer/actions/runs/39923292047) | E9，51文本；宿主重放，不新增设备 |
| 31 | 427148d8b52f7dfa920e7ebd05fd8f2f8c6b135b | [39961210476](https://github.com/yaoshining/ohos_ijkplayer/actions/runs/39961210476) | E10，17索引文本/87宿主检查 |

本基线已入库Phase23/24/28/parent-chain/31规格；Phase29/30分别在`tools/phase29-normal-terminal/spec`、`tools/phase30-consumer-handoff/spec`，不应误认为缺失；其余本机规格是否已入库逐份列SOURCE-INVENTORY，不通过旧路径猜测。

## 继续待验收

真实GPU内部调用永久不返回（调用边界hang/替换返回码不等价）、任意强并发/多实例和成功并发seek、未覆盖平台失败/fallback设备矩阵、物理HDR/客观亮度及全量主观声画、低API真机、TV正式产品集成和候选替换。已确认一次SDR观感与A02/B03有限范围不再笼统列“全部未验”。

Phase31当前库权威为`normal-library-binding.json`，`app/lib-binding.json`是保留的Phase28历史元数据，不能用于当前身份。TRACE正常与TEST/DIAGNOSTIC场景分别声明。异常退出后的进程/Ability/窗口消失不冒充应用keepScreen=false读回；正常路径才有该应用自清理证据。

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
