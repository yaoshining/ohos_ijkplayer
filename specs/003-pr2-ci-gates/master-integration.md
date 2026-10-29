# PR2 同步已审 master 的组合记录

2026-10-29 用户授权在既有 `codex/docs-pr2-speckit-closeout` 分支本地 merge 同步 master，保留祖先关系；推送、正文更新和远端 CI 需另经精确预览批准，PR #8 暂不合并。

## 固定身份与继承

- 旧 #8 head：`05dcf4acdc462d88fb94ce2d7f076e58cfc85bdb`。
- 已合并 #7 的 master：`c5828aeac29adae93b5a5f799ec8459a4cd025f9`。
- 本地纯 merge：`4c5382ed10a74cc027d34b3a806b4f2e4552a33a`，父序为旧 #8 head、上述 master。
- 纯 merge tree：`3a449c82f60ff13b45676a92e66bac7ad80f2a43`，与 GitHub 新组合 `dfd78e6bd896994c671c17d700d37c4204accf2c` 的 tree 相同；提交身份不同，不互称同一执行。

合并无冲突。master 的全部条目除 `.gitignore` 外逐 Git mode/OID 保持；PR2 原有 107 个变更路径除 `.gitignore` 外保持。PR1 严格静态输入集合修复及对应回归继承不变。`.gitignore` 同时保留 PR2 六个精确根和 PR1 原 `/out/`、`__pycache__/`、`*.pyc`。因此组合仍继承原宽 `/out/` 策略，不能声称拒绝其中所有未跟踪新文件；全部 tracked 字节与其他未忽略文件仍受原门禁约束。

本轮未修改产品、配方、来源锁或工作流，无新功能或缺陷实现，不编造新增 TDD RED。实际运行原有正常、关键边界和失败回归；输入全部物化并按精确 Git 对象核验，未放宽全集 inventory。

## 本地验证及证据范围

上述纯 merge 的 clean checkout：PR1 8 个命令通过，含 263 项 unittest 和 SDK 合同；PR2 12 个命令、101 项 unittest 通过。两套 runner 的前后输入、身份一致，`exactCommitReplay=true`。命令、结果及索引摘要见 [master-integration.json](master-integration.json)。最终随文档提交的精确重放、文件清单和审查结果由推送预览另行绑定，不拿本记录冒充其执行。

本地原始结果保留在本次审查材料；仓库只记录摘要，不声称未上传日志已可公开下载。最终推送后应核对真实 PR merge 的 checkout/parents 与新的宿主、Phase18、Phase20 结果。PR1 工作流路径过滤不匹配 PR2 原始变更，PR2 通过不等于新组合自动执行过 PR1 的全部目标构建。

## 历史任务承接与当前待验

旧 G006/G010 对应的预览与推送已推进到 `05dcf4…`；G007 对应旧 head 的三个远端 run：`39998335454`（PR2 宿主）、`39998335430`（Phase18）、`39998335365`（Phase20）平台状态成功。旧 checkbox/validation/失败原件保持历史时点，本轮没有重下载旧产物，也不把旧结果改挂新组合。

新组合的远端 CI、Phase18 十库/LP/mpv 双目录目标、Phase20 真实 Linux Samba 与双目录目标尚未执行；需要批准推送后取证。物理 HDR、主观声画、其他未覆盖设备项目继续待验收。`formalArtifactAllowed=false`，不替换候选/HAR/default SDK，不改 TV，不签名安装、不播放、不重跑长播、不变更系统设置。
