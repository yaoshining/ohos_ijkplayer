# 任务与证据范围

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
