# Phase11：跨目录构建修复与精确源码归因

2026-10-18。状态：本机及 Linux 各两次完整 clean、配对六库原始 SHA 门禁与 CI 下载实物复验通过；历史源码对齐的明确缺口保留。直接用户授权 `01a14eba-6fbb-78f2-b9ac-af6743965921` 已重新核实。默认生成器、候选/默认 SDK 和 TV 基线保持不变。运行目录接口沿用 phase9 提案，本轮未实施；真机 pending。

## 最小修复与测试

FFmpeg 的实际 configure 参数原先包含各自静态依赖根，导致配置字符串进入最终库后 A/B 不一致。现每个 fresh build 自身建立 `./deps`、`./toolchain` 两个独立入口；configure 与 pkg-config 实际使用相对入口，实际实体路径仍保存到 `input-bindings.json`，构建结束再次检查绑定，SDK 收录该证据。原有工具、静态输入和源码摘要前后验保留，没有改写生成配置字符串或最终库。

producer 最小改动为 `build-env.sh`、`build-ohcodec.sh`、`producer-sdk.py`。这三个文件及既有诊断 runner 修改前均保存旧字节，见 `out/phase11/previous-versions/archive-map.json`。新 `tools/cross-root-profile` 入口复用已验证的独立历史生成器流程，并要求配对 A/B 直接通过；不同物理根长度分别为 `a` 和 `longer-build-root-b`，不再以固定 root 对照替代。

- 路径测试保存真实 RED→GREEN；4 项测试覆盖不同长度/空格、真实 clang/pkg-config/静态库编译链接执行、缺失输入、预占/错误链接及绑定漂移。
- `producer-regression-v2.log`：138 项通过；`sdk-contract-review.log`：SDK 合同通过。原回归失败日志保留，失败源于宿主测试编译器/SDK 参数，修正后重跑。
- `pair-gate-red.log`→`pair-gate-green.log`：真实证明旧 fallback 会被调用，再改为配对不等直接失败；2 项通过。`hx509-regression.log`：21 项原诊断测试通过。

## 真实 configure 与调试对象层次

`out/phase11/configure-probe-v2/result.json` 使用实际固定 FFmpeg 源码、NDK 与复制到独立含空格路径的静态输入，执行真实 configure、pkg-config 和目标 `version.o` 编译。两侧配置字符串和依赖解析参数完全相同；该局部探针复用了旧静态输入，不计全链 clean。首轮补充探针误用 pkg-config 包名 `libsmbclient`，修正为源码实际使用的 `smbclient` 后另目录完成；原失败日志保留。

两份未剥离 `version.o` 原始 SHA 不同，DWARF `DW_AT_comp_dir` 如实保留各自物理工作目录。独立副本去调试段后相同，只作为差异定位；原对象未改写。交付六库原始 SHA 必须由实际完整构建比较，不能以这个副本结果代替。

含空格探针限定于本机 FFmpeg 阶段；本轮完整依赖链使用不同长度、无空格的根目录，不宣称整条依赖构建链已支持空格路径。

## 两次 clean 与 Linux CI

本机 `out/phase11/local-clean` 的 A/B 各自从固定归档建立生成器源码/安装目录、依赖源码/work/sysroot 及 FFmpeg；仅复用已锁定下载归档。两条链已成功完成，`pairedAllMatch=true`、`fixedRootAllMatch=null`，没有 fixed-root 输出。

独立复验 `local-verification.json` 通过：八目标静态归档及 headers/pc 共 111 项原始内容一致；每侧生成器 14 项 pin、实际 Waf 生成文件、依赖清单、构建记录、SDK 255 项 inventory 和实际输入绑定均核验。GMP/GnuTLS 目标配置及最终 Python 指针门禁通过。

两个 SDK manifest 分别为 `1f603e65842c2912015ee209fdb83f56f7afa5a12c86b0d8588548a854caad53`、`903caba9f57f8b773af1af67a1164ab3a7276cda9bfea4ec9e306012f3290c86`；manifest 保留不同实体目录等证据，本身不要求相等。六库原始 SHA 和开发文件全部相同；其中 avformat 为 `fb5a48e4a0962931a4392ecfd85f92047994d84a6a1bd9946d68fba3f8f9df11`。

六库仍各自不同于当前 TV；`local-vs-tv.json` 保留完整 SHA、节布局/BSS、导出审计，未发现导出名称增加/减少，不据此宣称行为等价。跨目录可重复性通过与历史 TV 字节一致明确分列。

专用 [CI 39124039398](https://github.com/yaoshining/ohos_ijkplayer/actions/runs/39124039398) 使用 `018d9c59665c515b29ef705f3ccef0798555d463`，已成功完成。日志确认 138 项默认回归、21 项诊断回归和 2 项配对门禁回归通过；实际 A/B 两条完整链均完成。首次手动 dispatch 因新 workflow 未登记返回 404，原结果保留于 `ci-start.json`；只追加专用分支/专用路径的 push 条件后实际启动。默认 workflow 未改，业务 checkout/index 未切换。

实际下载 artifact `12135723734`，127,949,407 字节，完整 ZIP SHA `11e2eb036bfce64466f6bbc2d2c5ba9f2298cabda564f03bf9d91d2ad5bd3430` 与 GitHub 登记值一致。`verify-ci-artifact.py` 对解压实物独立复验通过：每侧 23 项生成器/资源 pin、159 项依赖 manifest 内容、SDK 255 项 inventory；八目标归档及开发文件共 111 项一致，配对六库/headers/pc 全部原始 SHA 一致，无 fixed-root 输出。实际绑定记录分别指向各自 sysroot，构建中的软链后验由成功构建门禁提供；ZIP 核验不冒称恢复了 CI 运行时软链。

Linux SDK manifest 分别为 `a1863bf6d60384e167d13ef098b964a86db362f8768ba90fa1400feabd210332`、`dda0c0aafbc518e49ede549cd4f659c15085554dbd7c5c458de0820c2b6874f4`；avformat 为 `53a228d0728cc15bc4ec5a7f8a60f695421cec650ef99211f9250d41136e504a`。实际 GMP/GnuTLS 配置与最终 Python 指针检查通过。详见 `ci-verification.json`、`ci-*-actual-features.json`、`ci-*-python-runtime.json`。系统兼容库/M4 复用 phase10 独立重取的固定 Debian 归档字节作摘要参照，不冒称本轮再次下载或随 ZIP 交付所有宿主工具。

Linux 与本机 NDK 分列；Linux OpenHarmony5.0 诊断输入不同于本机 API24，未要求跨工具链字节相等。`linux-vs-tv.json` 与 `local-vs-tv.json` 分别保存当前六库对 TV 的全文/节/导出矩阵；两平台所有六库都仍不同于 TV。

## avformat 源码归因与冲突

当前 TV 两个有效 Python 指针均指向历史宿主 `…/smb-src/samba/bin/python`；现行构建指向 `/usr/local/samba/lib/python3/site-packages`。保留目标路径修复与全文 SHA 等于当前 TV 不能同时成立，已先向用户报告。保留目标配置；TV 仍是比较基线，不替换候选，也不把目标目录存在/权限当作已验证。

`out/phase11/source-research/report.md` 记录分项证据及局限：Samba 三运行路径对象可从精确源码分别复现当前与历史参数对象；version 对象的历史配置控制复现不等于历史 configure 来源闭包；GnuTLS 的 24 个差异对象已从固定源码重编译，配合其余 367 个可追溯现行源构建对象，重新归档完整 SHA 等于历史。这不计作 391 对象全新 clean，不复制历史对象回填。

未选入代码但影响 stdin GOT 的 `lex.lex.c.124.o` 属于另一项 Flex 2.6.4 生成任务。固定官方 upstream 2.6.4 已实际源码构建、生成并目标编译；与当前 Xcode 2.6.4 的对照均不等历史 C/对象。历史与官方源码在 yyleng、yy_n_chars、yy_scan_bytes 长度类型上不同；Xcode 还有 yy_buf_size 和 SIZE_MAX 边界代码差异。相同版本号不能建立精确来源身份，来源缺口保留；不扩大 HX509 特例、不手改生成 C、不回填历史对象或更改默认归档。解析器故障注入与 sanitizer 继续暂停。三方逐项证据和固定官方发布链接见研究报告。

## 冻结证据与研究副作用

本轮方案核查时，19,052 项上轮封存文件、旧源码归档、候选/默认指针、TV HEAD/HAR/mpv/六库及业务 HEAD/index 已独立复验通过：`out/phase11/solution-review-boundary.json`。runner 的有意修改后，又经 previous-versions 映射全量重验通过：`old-index-with-map.json`。归档映射共 5 条，旧索引实际引用其中 2 条（run.py、旧 workflow），不混淆数量。

最终 `final-boundary.json` 复验通过：上轮 19,052 项、17 项既有 pin、15 项业务文件、三来源锁及 86 项 producer 文件按有意修改归档映射核验；候选与默认 SDK 的 inventory 完整校验，TV HEAD/HAR/mpv/六库、业务 HEAD/原 Git index 与旧 producer 分支均不变。当前诊断分支只用于本轮代码/报告和 CI；新证据索引与 handoff 独立置于 `out/phase11`，不替换上轮交接。

研究中旧 FFmpeg 树的 `make -n` 触发 included makefile 重建，更新了版本头及空 `.version` 的 mtime。已用同轮 B 的 8.0 头恢复，恢复后源码重编译对象也与原对象一致。该头不在旧封存索引，不能声称索引证明其原始字节；依据和副作用完整记录于 `source-research/dry-run-side-effect/incident.json`。19,052 项封存字节复验无差异。后续研究只在独立副本运行 make，包括 dry-run。
