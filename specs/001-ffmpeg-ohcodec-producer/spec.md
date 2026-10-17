# 功能规格：以 TV 字节基线迁移 FFmpeg/OHCodec producer

日期：2026-10-17。状态：producer 实现与静态验证完成；重建字节不同、设备 pending。工作分支保留 `yaoshining-hdr-playback`，不切分支。

## 用户场景与验收

### US1（P1）：Player 消费明确的 SDK

Player 需要一个绑定六库 SHA256 的 producer manifest，不能通过 tag、cache 或版本猜测组合。
给定 TV HEAD `4a004afb5ea036ee12cf479cfcdd29b5e610c1e4`、HAR SHA256 `826b667dcd315e75e71f89065c3aef4bd60ea73743916ee629469f93228c66a9`、HAR 内 ARM64 libmpv SHA256 `3ae9969ac13a58aaa5827520a44e56461f566aff66b9bdd7fe4b78f0da31b076`，导入时逐项验证当前字节；任一差异拒绝导入并报告。只导入准确的 FFmpeg 六库和证据，不把旧 delivery HAR 当基线。

### US2（P1）：独立重建与差异报告

固定 FFmpeg `140fd653aed8cad774f991ba083e2d01e86420c7`；固定 libmpv-ohos-build `1bab837e662ffa47ce51efd0720d3ed7c4988944` 的 AV3A、zero-copy 补丁，加本仓 SMB 凭据补丁。启用 GnuTLS、OHCodec。重建写入全新目录，六库逐项对比，不同字节不得替换 imported-baseline。

### US3（P1）：状态可审计

SDK 记录源码、补丁、工具链、静态输入、runtime、headers/pkgconfig、许可证及 SBOM 引用。缓存八份静态库必须匹配交付摘要；即使匹配也标注未全依赖源码重建。每个 SDK 独立标记 imported-baseline/source-build，deviceAcceptanceStatus 永远 pending，不继承旧设备记录。

## 功能要求

- FR-001：ohos_ijkplayer 唯一生产 FFmpeg/OHCodec 与 SMB/TLS 依赖；VidAll_Player 只消费固定 producer manifest，生产 mpv、HAR、组合清单；VidAll_TV 只集成统一组合并验收。
- FR-002：保留当前工作树所有既有改动，不读取 keys；仅修改 tools/ffmpeg8、对应工作流和配套文档。不改 Player/TV，不推送、发布或操作设备。
- FR-003：产物清单包含 schemaVersion、producer.repository/revision/workingTreePatchSha256、baseline.tvCommit/harSha256、targetAbi、sources、patches、tools、libraries(name/path/sha256/sizeBytes)、headers、pkgconfig、licenses、sbom、rebuildComparison、deviceAcceptanceStatus。
- FR-004：校验拒绝缺文件、摘要或尺寸不符、目录逃逸、不完整六库集合；导入与重建不得覆盖已有目录。
- FR-005：docs/vidall-tv-baseline-handoff.json 始终指向可消费的 imported-baseline；重建独立报告，包含文档路径与剩余缺口。
- FR-006：先运行现有回归，再编写失败行为测试，随后实现；记录真实顺序。

## 成功标准与边界

六库导入字节全部一致；生产链可在固定输入下执行并记录结果；重建差异被完整披露；摘要篡改回归拒绝通过；真机 pending。首期 ARM64，历史 x86_64 普通构建不宣称 OHCodec 基线。完整依赖源码重建、设备、Player/HAR 组合验收不在本次完成承诺内。

## 冻结边界追加（2026-10-17）

用户底线：不改变 VidAll_Player 内任何内容，包括源码、二进制、候选库、锁、清单、证据及 Spec Kit 文档。VidAll_TV 同样只读。本会话截至此规则追加时没有写入上述两个项目任何文件；后续全部文档与产物仅在 ohos_ijkplayer。不得自行回滚其他会话或用户改动。

## 第二阶段：可重复构建、正式 Spec Kit 和闭包门禁（新增授权）

- FR-007：定位具体函数/地址/重定位差异；将历史字节复现与新的两次 clean 字节一致分开验收，不覆盖导入包。
- FR-008：官方稳定 Spec Kit 在本仓隔离安装；初始化真正 .specify/宪章/feature 状态及官方脚本/命令，保留旧文档与真实顺序。
- FR-009：CI 调用 OHCodec producer，验证固定源/补丁/工具/依赖与 SDK；两次 clean 比较，缺完整来源闭包时正式产物明确失败，不能普通 SDK 代替。
- FR-010：新下载必须由统一 SHA256 来源锁验证；新 release 与历史 git/缓存证据分开。真实推进八库源码构建，缺证逐项记录。

## 第三阶段：实际闭包与远程 CI（追加授权）

- FR-011：八库及所有交付头文件/pkgconfig 必须在独立 fresh source/work/install 路径实际构建两次比较，仅共享摘要通过的源码下载；报告绑定实际 inputs、recipe、NDK、宿主锁与产物。
- FR-012：宿主工具在构建前冻结并验证；Linux 容器基础镜像固定摘要、包固定签名快照并记录版本/下载摘要。macOS 历史环境和 Linux 新选环境分别记录；漂移拒绝运行。
- FR-013：允许专用分支/提交和必要 push/CI 验证，原脏工作树和当前分支不切换。公开提交排除 keys、out、用户缓存、业务改动和私有媒体数据。不得发布、合并或部署。此授权取代 FR-002 与宪章第五原则中的本轮禁止推送部分，其余冻结边界保持。
- FR-014：新选来源闭包、历史身份、静态依赖重复性、FFmpeg 重复性、设备状态独立表示；历史缺证不因新的成功自动消失。
