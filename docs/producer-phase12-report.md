# Phase12：历史 lexer 已从固定 Apple 源码精确复现

2026-10-18（Asia/Shanghai）。本轮按主会话 20:15 的直接人类授权 `01a14eef-d3aa-7453-b741-4daeea19cd5a` 完成来源调查、Spec Kit/TDD、全新 Flex 构建、lexer 生成/目标编译及 avformat 源码归档对照。运行目录 API 不在本轮实施范围。默认生成器、候选/默认 SDK 与 TV 基线不变，Player/TV 全目录只读，设备 pending。

## 结论与来源纠错

历史 `lex.lex.c.124.o` 已由公开固定源码重新生成并编译，生成 C 与完整对象均全字节匹配。之前把 Apple `flex-35` 标签解释为上游 2.5.35 的排除依据错误：该固定提交的 `configure.ac`、实际 `flex --version` 和生成 C 均为 2.6.4；不存在本例“工具版本和生成 C 版本不一致”的事实。旧报告/证据保持原字节，本报告更正该判断。

来源为 [Apple flex-35 固定提交](https://github.com/apple-oss-distributions/flex/tree/8548f53e24244c0a411dea128a21686b61d29df4)，完整 revision `8548f53e24244c0a411dea128a21686b61d29df4`；[原归档](https://codeload.github.com/apple-oss-distributions/flex/tar.gz/8548f53e24244c0a411dea128a21686b61d29df4) SHA `ba130fc9fccbb61470aed73a3f726ddc90fe42e1f10b30bf1b1a805232710131`。本轮重新获取原归档，与既有锁定字节相同。直接构建该 Apple 源码，无追加补丁、无反向编辑生成 C，无历史对象回填。它提供可精确复现的完整源码集合，不证明历史机器实际安装包或 Apple 导入前每个补丁的独立历史。

原 `src/skel.c` SHA `6a463b4d016d1eaafd212041b8182db6e9ff4e6e9be992fb71e2b25d678114e7`，实际编入工具且构建前后不变；原 `scan.c` 也不变。`flex.skl` 与预生成 `skel.c` 分别绑定，不能仅检查前者推断实际工具。`SIZE_MAX` 定义不等于当前 Xcode 的扩容保护分支；历史类型组合和完整原始输出分别验证。

## 全新工具和真实目标对象

`out/phase12/downstream-research/native-build-v2` 从原包建立全新目录，真实执行 configure、bootstrap stage1scan、final make，三条命令退出码均为 0；没有全局安装。实际编译 bootstrap 250 项、final 251 项输入有编译前/后 SHA 验证。Flex 二进制 SHA `51d5c29eb5f96a8f253e190d6a2a5b5ed58c83ab98008178599aca592a7340f1`，与 Phase10 固定源码构建工具相同。

失败证据完整保留：首次新目录构建因预采集遗漏 `SDKSettings.json` 被门禁拒绝，另起 v2 重建；v2 最后对“所有原包文件均不变”的检查发现 configure 正常生成 `src/config.h`。独立核验限定唯一合法输出例外，保存 config.h 差异及实际编译前后 pin，未忽略其他源码漂移。构建后解析了 M4/make 调度入口的实际后端，未冒称后端均已预锁；完整宿主运行环境源码闭包仍未证明。

先用既有源码工具在 `generation-controls/apple-reused` 重放，再用本次 fresh 工具在 `apple-fresh` 重放，两者均重新生成相同 Samba com_err `lex.l`/`parse.y`，原输入逐字节核对固定 Samba 归档。GNU Bison 2.3 + Apple data 复用既有已锁定工具；本次生成阶段直接绑定实际 Xcode M4 后端，原 stdout 与 Waf UTF-8 解码/通用换行/latin-1 写出分别留存。

| 产物 | SHA256 | 结果 |
|---|---|---|
| parse.tab.c | `16abd84d852c8e60b635632d69558de181f0738e798f3cc22c9754d02c5ea3a3` | 历史一致 |
| parse.tab.h | `d8228eeb997ea87919f61b2b084fb1acbd7546caa979cb0254de2829883133f5` | 历史一致 |
| lex.lex.c | `4815000afa455ee8fb5b8fc85b4c6172402adc84798ef8d1690ed781b090b549` | 历史一致 |
| lex.lex.c.124.o | `6eb055d999f8936b71e5dab8660f052c2c0c1ebaa25ac061fedcdad1a4a86918` | 历史一致 |

两次目标编译各 103 项实际依赖均预先记录并后验无漂移，命令、flags、头文件与对象保存于各 comparison.json。来源/生成/编译门禁正式通过，见 `out/phase12/source-verification.json`。这证明当前固定源码可复现历史输出，不等于历史安装身份成立，也不计整个依赖链全新 clean。

## avformat 源码归档与链接

两份新归档均以 Phase10 的可追溯源码成员为基础，保留 historical occurrence/顺序映射。运行路径对象使用 Phase11 固定源码重编译的 `historical-except-python-control`，GnuTLS 使用 Phase11 的 24 个重编译对象加 367 个既有源码对象组成的归档，FFmpeg version 使用 Phase11 源码加历史配置控制对象。它们均为源码输入，未从历史归档复制任何对象；旧归档序列仅用作元数据参照。这是隔离历史参数诊断，不更改默认 recipe，也不是全链新构建。

| 对照 | Samba 成员数 | 最终 avformat SHA256 |
|---|---:|---|
| 保留 Python 修复，不添加 lexer | 1266 | `a6e99ee7a6a1e7bb50927ea3e8f1ecd21660d1b83e29614c9d8420c2cc28cbef` |
| 同上，加入本轮源码 lexer | 1267 | `d9e0dfaa27d3f64fe3b44c4c60d6d9b07bf9b83a5a0bc6684bf7f413619f159e` |

两份库之间仅 `.text` 和 `.rela.dyn` 改变：4 条指令、42 个重定位项；stdin GOT 从 `0x124a2a8` 移至 `0x124a2d8`。link map 确认该 lexer 本身仍未选入代码，复现其归档符号顺序影响。每项成员来源、响应文件、工具/553 个 FFmpeg 对象及其他输入、map、反汇编和 Python 指针证据均保存于 `out/phase12/relink-controls`。

加入 lexer 后仍不等于 TV 的 `79a66254…1073b4`。TV stdin GOT 为 `0x124a308`；当前对照 `.rodata` 比 TV 小 16 字节，`.text` 起点前移 64 字节且大小增加 8 字节，`.data/.data.rel.ro` 内容相同但位置前移 48 字节，BSS 大小相同。导出名称和已检查的元数据无增删/变化，不据此宣称行为等价。没有执行恢复宿主 Python 的控制，不将全部剩余差异宣称已唯一归因。

两个最终对照都通过 Python 门禁：有效指针指向 `/usr/local/samba/lib/python3/site-packages`，没有宿主 Python 路径。保留修复与全文 SHA 等于当前含历史宿主路径的 TV 无法同时成立，继续保留修复；未创建目标 Python 目录或推断设备权限。

## TDD、CI 与调查范围

新增 `tools/lexer-source-profile` 只核验诊断记录：来源包/原补丁/实际骨架输入 pin、工具/M4/头文件/原始 C/对象漂移、版本/特征伪阳性、真实 Waf 输出转换、编译输入关联和失败退出码。`profile-red.log`、`profile-red-v2.log` 保留缺失实现时的真实失败；最小实现后 16 项 GREEN，再补充已具备行为的 SIZE_MAX 定义及发行标签边界回归，共 18 项通过。没有把下载或构建故障当作 TDD RED。

[专用 CI 39127921005](https://github.com/yaoshining/ohos_ijkplayer/actions/runs/39127921005) 在诊断提交 `ae39397e81f9e598856f8ded5f3bac1fc1b104d6` 成功：18 项新门禁、8 项 Python 路径回归、21 项 HX509 回归，本机同样通过。下载制品 `12135804839` 为 2022 字节，ZIP SHA `0ed58feaf393a7511c390511a63f59f5c94cf35f928d368df549d497fe7bbff6` 与官方值一致，解压日志和提交号核验通过。CI 是 Linux 门禁回归，不是本轮 Linux 生成器/SDK 全链重建；Phase11 双平台两次 clean 证据保持引用。

upstream 2.6.0–2.6.4 骨架、当前 Homebrew、Debian、Android、ANGLE 原输入及排除范围都有固定 revision/SHA。Homebrew 历史 API 的 500 保留为检索缺口。已找到 Apple 完整源码复现，无需反向套用其他来源补丁。来源研究旧 66 项和新 1082 项均独立摘要复核；历史归档同版本不等于同补丁的结论仍成立。

## 交接边界

Spec Kit 已完成 spec/plan/research/data-model/tasks、官方 prerequisite、只读语义分析与实施；前一轮误停在方案复核的快照保存在 `out/phase12/planning-snapshot`，未抹去过程。运行目录 API 未实施，已暂停的解析器故障注入与 sanitizer 未恢复。

最终边界详见 `out/phase12/final-boundary.json`；新索引与交接独立置于 `out/phase12/evidence-index.json`、`handoff.json`。保留旧封存字节、候选及默认 SDK、TV HEAD/HAR/mpv/六库、业务分支 HEAD/index 和既有业务改动。诊断代码只提交既有诊断分支，不切换业务 checkout。`formalArtifactAllowed=false`，`deviceAcceptanceStatus=pending`。
