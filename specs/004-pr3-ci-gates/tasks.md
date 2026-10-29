# 任务与证据范围

> 最终状态更新（2026-10-29）：合并、默认分支 CI 和仍待验收范围见[最终收尾索引](../CLOSEOUT-20261029.md)。下文保留历史时点原文；早期“未推送／未合并／待 CI”不再代表已完成过程的当前状态，旧失败和未验证项不改写。

- [x] G001 新增 spec/plan；旧阶段封存不回写。
- [x] G002 门禁回归先 RED 后 GREEN。最初缺实现 RED 仅证明测试入口；后续补旧 workflow 不含 PR 矩阵、漏矩阵项和完整 CLI 聚合提前返回的语义负例。最终 18 项覆盖真实子进程、超时/缺工具、零测试、索引、UTF-8/NUL/ELF/symlink、真实 Git PR/merge_group/manual 身份、浅克隆恢复、第二/末项证据损坏。
- [x] G003 新增 PR、master push、merge_group、手动完整矩阵。required 实际下载所有证据、核验 11 项和精确索引/身份，任一失败不得绿色聚合。
- [x] G004 本地实现提交 `2562bbd5b906a8233b2f6e06efe14555e030ab99` 完整 11/11 宿主重放通过，18 项门禁测试通过。Phase27/28 初次 TLS 断连保留为失败，同 SHA 新目录重试成功。证据绑定此 SHA，不冒称未来远端 CI。
- [x] G005 临时组合 `4530f7f1f24e5f00a92275f518d1b37042b126ca` 的 PR1/PR2 runner 及 PR3 11 项均通过，输入/身份前后不变。来源为 PR1 `a1ea31140306e95f3c98b4bfe81f81a16d51ef92`、PR2 `615b3bdb0e7ee1195cfb37c2576d9066757da99d`、PR3 `2562bbd5b906a8233b2f6e06efe14555e030ab99`；临时组合没有推送。
- [x] G006a 整理精确提交本地预览；等待审查和用户批准，不代表推送授权。
- [ ] G006b 批准最终 SHA 后推送，核对远端相同 SHA/merge SHA CI 及制品。
- [ ] G007 本轮组合目标 native 库构建与后续设备验收；不能由宿主通过代替。

本机审查材料在 `/private/tmp/pr3-preview-20261024/`、`/private/tmp/pr3-final-aggregate.json` 和 `/private/tmp/producer-combination-evidence-20261024/`，是本地补充，不是仓库内永久原始证据。将来远端 artifact 才是新增远端验证记录。文档收尾提交应单独核对代码与上述实现 SHA 的一致性，不能改写历史运行身份。

1639 条来源文件审计中仅两条与 PR3 原继承值不同：`.github/workflows/phase18-dependency-closure.yml`、`.github/workflows/phase20-runtime-directories.yml` 采用 PR2 新本地候选的工作流修改（待用户批准推送），其余完全相同。无源冲突。Python 目标目录回归和默认 SDK 合同包含在组合 PR1 runner 内。未改实际 SDK/default 指针、Player、TV 或候选产物。

目标设备、物理 HDR/主观声画、真实 GPU 永不返回和任意强并发未在本轮验证，继续待验收。60 分钟长播不是接入前置条件，本轮不运行。`formalArtifactAllowed=false`。

## 远端首次执行与身份兼容返修

已批准 `e8e495ba4db52a1b076860951d1cdd301b7424ca` 已推送。远端 run `39995466079` 为 failure：11 项均在身份检查处拒绝（commands=[]），required 亦失败，未执行阶段测试；不能记作阶段功能失败或通过。11 个失败 artifact 索引已经本机逐字节核验。

GitHub 记录的 event base 为旧 `a73e23173d684c31056b50f353ac4321fbcd812b`，实际 checkout 为把已批准 head 合入新 `615b3bdb0e7ee1195cfb37c2576d9066757da99d` 的 merge。修复保留声明 base 与实际第一父两份身份，强制可信 GITHUB_SHA、PR merge ref、base ref、两父与精确第二父，并验证声明 base 存在且为实际第一父祖先；不取可变远端分支替换输入。

- [x] R001 真实 Git “事件 base 落后于实际 merge base”语义 RED；无关 base、缺失 base、错 head/ref/SHA 负例。
- [x] R002 最小身份修复，19 项门禁回归 GREEN。
- [x] R003 本地完整 workflow 事件环境重放：实现 head `fe0f558ef05fe2b68e744888786e8639fc190240`、实际 base `615b3bdb0e7ee1195cfb37c2576d9066757da99d`，临时 merge `51ab1fab6d8f5b3bca033f5f5486ca210533b2b0`；event 声明 base 仍为旧 a73。19 项门禁回归、11/11 实际阶段矩阵、required 全量聚合和索引校验通过。独立审查与最终推送仍另行处理。
- [ ] R004 新修复精确提交预览、用户批准后推送；原批准不覆盖新 SHA。

原 run 失败保留；未推修复、未合并，目标产物与真机范围仍按上文待验收。

R003 本机证据：`/private/tmp/pr3-repair-event-evidence/aggregate.json` 与 `event-environment.json`。以上为本地模拟真实 GitHub 事件环境，不是新的远端 CI；最终规格文档提交通过与实现 SHA 的代码/工作流等价核验，不能冒称其本身重跑了完整 11 项。拒绝身份时输出保留声明 base/head/ref、实际 SHA/父链和环境 ref，方便失败追溯。

## 第二次远端失败与受限嵌套组合

已批准的 `882a1c548175f793771877a090ae1169bf2453e6` 已推送。run `39998466471` failure，11 项仍在身份门禁处拒绝（commands=[]）。这次是环境 `GITHUB_BASE_REF=master` 与 event 声明 `codex/docs-pr2-speckit-closeout` 不同；没有证据显示 PR 被人为 retarget。实际 checkout `5644f3aa4c4a7087c1651f042729f580ec1cd2d8` 的第一父是 PR2 中间 merge `e712d27ef548f91ca408ae38dc7a7ecd91601a86`。

实际 Git 对象核验：中间 merge 两父按顺序为 `1bb2a7c33ed88eafbeb3f42bcc4bf4299797497b`、`05dcf4acdc462d88fb94ce2d7f076e58cfc85bdb`，tree 为 `c74b46a5b1a9dc1c4a591d247e88f94eab6619b6`。工作流没有覆盖 GITHUB_BASE_REF。

新增 tracked `combination-lock.json` 只允许以上确切 root/dependency/tree 及特定 ref 对应的 `locked-nested-combination` 模式；普通 PR 同 ref 模式不变，其他漂移继续拒绝。仍保留精确 GITHUB_SHA、PR merge ref、最终两父/head、声明 base 到固定依赖的祖先检查。锁只在审查后显式更新，不跟随远端分支。

- [x] N001 冻结真实失败，核验实际 Git 父链/tree；真实临时 Git 嵌套模式 RED→GREEN。
- [x] N002 20 项门禁回归，包含锁缺失/格式、ref、root/dependency/tree、父顺序以及普通模式原有负例。
- [x] N003 完整事件环境重放：实现 head `0596742ff1f4c4d630f2f077633b61039a6ea2de`、临时嵌套 merge `bab4c7b5946b9c15ab43fb1f6ee14af883f14884`；先行 20 项门禁自测、11/11 原阶段门禁和 required 全索引/同身份聚合通过。环境 baseRef=master、event 声明 ref=docs-pr2、声明 base=a73，输出明确标为 locked-nested-combination。
- [ ] N004 精确修复预览、批准后推送；未批准的新 SHA 不推送。

这项组合证据不得标成普通 PR merge。旧远端失败不改写，产品源码、TV、候选和历史封存不改。

N003 本机证据 `/private/tmp/pr3-nested-event-evidence/aggregate.json`。Phase27 初始 `27/` 和第一次重试 `retry27/` 两次 TLS EOF 原样保留；第二次重试 `retry27b/` 使用同代码、同原始网络参数实际下载锁定来源并完成全阶段成功，没有替换执行器或伪造缓存下载。其余 10 项初次通过。后补的两条真实 DAG 负例分别证明同父但额外 tree 修改、声明 base 在中间祖先却不在依赖祖先均被拒绝；删除对应守卫的两个变异体也被相同回归拒绝。最后收尾只增加测试负例和本规格记录，运行 gate/锁/workflow 与已测实现逐 blob 等价；最终提交以 clean 20 回归、等价核验确认，不冒称最终测试文档 SHA 重新运行 11 阶段。新远端 CI 仍待新精确 SHA 获批。

## 第三次远端执行：宿主依赖与隐藏证据文件返修

已批准的 `aa5b1a94c7af680780306ac02f4910e68d20d46a` 已推送。run `40002611218` 在锁定嵌套输入 `fb3548d8e336101e01c57d59c5ac0c922be69d16` 上通过身份检查。10 个阶段 job 成功；Phase21 因 Ubuntu runner 缺少宿主 `libavutil-dev`，实际 C preflight 测试类被跳过，日志为 24 tests / skipped=1，严格门禁和 required 正确失败。这个结果不代表 11 项通过。

下载后另发现 Phase26/27/28 各缺一份 `child/execution/.github/workflows/phaseNN-validation.yml`：原索引含这些文件，但 upload-artifact 默认排除隐藏目录。10 个 job success 不能表述为十份完整证据索引通过。其他已有文件字节未漂移；旧失败和不完整制品均保留。

- [x] D001 Linux/amd64 Ubuntu22 容器、只读源码、独立输出，uid/gid 1000 真实重现缺依赖 RED（24 tests / skipped=1）；既有门禁拒绝 skipped，不改变旧测试或成功标准。
- [x] D002 仅 case21 安装 pkg-config/libavutil-dev；同一非 root 用户真实运行 13 项 C preflight 及全套 37 项 Phase21 测试，均无 skip。记录 apt/dpkg/pc flags/库文件哈希和 uid；这是宿主测试 FFmpeg4.4.2/libavutil56，不能冒称目标 FFmpeg8 来源或重建。
- [x] D003 仅已有受控 `pr3-${case}/artifact/` 上传开启 include-hidden-files，路径不扩大。真实创建带索引隐藏 workflow、删除该文件的负例被完整索引验证器拒绝。Phase21 依赖身份另存 `pr3-host-dependencies-21`，不混入 required 的 pr3-contract-* 集合。
- [x] D004 22 项门禁回归通过；所有 workflow 通过 actionlint 1.7.12 语法/表达式检查（本机无 shellcheck/pyflakes，显式关闭这两项，不能声称它们通过）。新提交只包含 CI、新测试和本规格文档；gate.py、锁和全部旧阶段源码/测试未改，不重复无关 11 阶段。
- [ ] D005 新精确 SHA 预览、独立审查、用户批准后推送并重跑远端 11 项与 required；本地 37 项不替代新远端 CI。

本机证据 `/private/tmp/pr3-phase21-linux-evidence/` 与 `/private/tmp/pr3-phase21-hidden-tests.log`；Ubuntu amd64 子 manifest `sha256:a8fe6fd30333dc60fc5306982a7c51385c2091af1e0ee887166b40a905691fd0`。初次本地尝试 `/private/tmp/pr3-phase21-linux-attempt01/` 在 RED 后因审计脚本误查 libavutil57 而停止；实际为 libavutil56，修正记录脚本后全新输出运行通过，初次失败保留。三 PR 临时组合与本次远端锁定 master+#8+#9 为不同身份，不互相继承通过声明。未改产品、Player、TV、候选或旧封存；不运行设备与长播，未验证项继续待验收，`formalArtifactAllowed=false`。
