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

## 第四阶段：差异归因与历史身份调查（2026-10-18）

- FR-015：fresh核验完整TV组合；不一致先告知，保持所有旧包和锁。
- FR-016：对TV、历史复现、macOS API24与Linux5.0逐层检查ELF节、符号、配置及对象；通过隔离实验区分路径、工具链、源码/补丁及静态依赖影响，不将所有差异归为debug。
- FR-017：历史记录、缓存Git/归档/配置/对象及官方SDK证据只读收集，分别标记proven/inferred/missing；当前文件相同或可复现不能单独证明历史使用身份。
- FR-018：API24/6.1.1.115 Beta1与Linux5.0严格区分；缺失的历史记录如实保留，设备pending、正式发布false。

## 第五阶段：恢复GnuTLS能力与GMP基线配置（2026-10-18授权）

- FR-019：修复GnuTLS静态传递依赖漏-lgmp，真实链接与configure能力测试覆盖失败/正常/边界；断言NON_SUITEB及真实曲线表含SECP192R1/224R1。
- FR-020：新诊断GMP显式--disable-assembly及--without-readline，断言NO_ASM=1与generic参数。保留--with-pic，配置路径/宿主差异单列，不声称与历史完全相同。
- FR-021：本机两次全fresh静态+FFmpeg构建及独立比较，专用分支最小提交真实CI并下载复核；现有冻结包、候选、来源锁不替换。
- FR-022：能力断言进入构建与CI门禁；HAVE_ICONV/Samba既有差异不扩展修复。新闭包、历史身份、基线差异、设备状态独立。

## 第六阶段：剩余配置差异对齐（2026-10-18授权）

- FR-023：从实际历史cache配置/日志、源码补丁、归档对象及TV绑定记录追查GnuTLS硬件加速、压缩包装、HAVE_ICONV与Samba平台/生成器/路径差异；先报告逐项方案再实施。
- FR-024：真实配置/编译/链接RED先于最小修复；禁止单纯补宏或把宿主宏机械改成目标宏。保留第五阶段GMP与曲线门禁，新增实际能力/路径验证。
- FR-025：历史绝对运行路径与可迁移交付冲突须显式报告，独立诊断实验区分历史配置复现与可重复交付。现有来源锁不改；必要新来源先解释，不覆盖旧证据。
- FR-026：新out/phase6内两clean静态+FFmpeg、实际CI及下载核验；旧候选/默认指针保持，Player/TV只读、设备pending、formalArtifactAllowed=false。本阶段授权扩展FR-022中的不修复范围，沿用FR-013专用分支权限。

## 第七阶段：Bison与目标路径方案确认（2026-10-18）

- FR-027：先提供带实物证据的方案，再修改默认配方。独立调查仅写新out/phase7；Bison2.3实验不得覆盖现有来源锁，不追认历史工具执行身份。
- FR-028：Python路径需表示目标安装布局，保留禁用Python状态和宿主构建解释器；不得用空路径、伪造能力宏或删除字符串冒充功能修复。其他运行目录区分只读资源、配置、可写状态及无客户端消费者项。
- FR-029：六库差异分别记录完整SHA、节内容与布局、代码/数据/重定位、配置字符串、生成器贡献及动态导出。控制实验不能替代两clean、CI、组合或设备验收。
- FR-030：候选/默认SDK、phase6证据、Player和TV保持冻结；未确认的方案不得记作实施完成。后续经确认实施时沿用真实RED→最小修复→GREEN与实际对象门禁，最终配方冻结后再进行两clean及CI实物核验。

## 第八阶段：Python目标路径与实际工具锁修复（2026-10-18明确授权）

- FR-031：目标Samba显式Python安装目录固定为/usr/local/samba/lib/python3/site-packages，保留disable-python及真实宿主解释器；门禁核验实际命名指针、禁用状态和最终avformat相对重定位/宿主路径。明确这不是Python模块交付或沙箱可用保证。
- FR-032：按实际PATH区分Apple转发器与直接工具，冻结实际执行文件、选择器状态、Bison骨架、编译器resource及明确子工具；缺失、漂移、资源集合增删、选择器变化失败。父预锁与受控子进程及native env-i选择器一致。Linux保持自身工具与获取链语义，不宣称完整Xcode/SDK或历史身份。
- FR-033：真实RED先于修复，覆盖正常、边界、失败和用户环境注入；最终配方冻结后，两fresh静态source/work/sysroot与两FFmpeg构建、真实专用分支CI和外部artifact绑定下载复验；更新六库与TV实际差异。
- FR-034：全部新输出out/phase8；phase6/7证据、来源锁、默认SDK/候选、原业务分支/脏改动与keys保持；Player/TV全目录只读，设备pending、formalArtifactAllowed=false。沿用专用分支推送授权，不合并发布。Bison/Flex保持现有默认，运行目录API不在本轮实施。
