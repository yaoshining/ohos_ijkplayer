# 本仓 Spec Kit

本仓此前没有 `.specify`，此次是**初始化到官方稳定 v1.2.1**，不是把已有项目从 0.12.11 升级。本会话未升级全局 CLI；开工观察为 0.12.11，收尾再次观察已为 1.2.1，变化来源未由本会话确认。精确官方提交/归档摘要在 version-lock.json。

官方 CLI 安装于 `out/spec-kit-cli`；调用 `bash tools/speckit/specify ...`。重建隔离环境：按 version-lock.json 下载官方 archive 并校验 SHA256；解压后 `uv venv out/spec-kit-cli`，使用 `uv pip install --python out/spec-kit-cli/bin/python -r tools/speckit/python-dependencies.lock.txt` 和同一 Python 安装解压目录。不得全局 self upgrade，不改 Player/TV。

真实初始化命令：`specify init --here --integration codex --script sh --force --ignore-agent-tools`，官方安装 `.agents/skills/speckit-*`、`.specify` 模板/脚本/工作流。已有 specs 内容没有覆盖；项目宪章随后按用户规则完成。

选择已有 feature：

```bash
SPECIFY_FEATURE_DIRECTORY=specs/001-ffmpeg-ohcodec-producer .specify/scripts/bash/setup-plan.sh --json
.specify/scripts/bash/check-prerequisites.sh --json --require-spec --require-tasks --include-tasks
.specify/scripts/bash/check-prerequisites.sh --json --require-tasks --include-tasks
bash tools/speckit/specify workflow list
```

v1.2.1 使用 SPECIFY_FEATURE_DIRECTORY；本次旧的 SPECIFY_FEATURE 调用曾失败，之后按官方提示修正，证据保留。setup-plan 会保留已有 plan，并持久化 .specify/feature.json。Codex 使用 `$speckit-analyze` 与 `$speckit-implement` skills；语义分析在现有会话中依据官方步骤完成，不能用 prerequisites 退出码冒充语义审批。

官方 Full SDD Cycle 已安装；其 review gate 是真实人工关卡。本次不新开自动 agent 工作流，不虚构 gate approval，继续执行用户已经明确授权的当前开发。后续更新已有 integration 使用官方 `specify integration upgrade codex`，先保存宪章、feature 和 specs，固定版本后检查差异。
