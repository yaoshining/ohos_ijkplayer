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
