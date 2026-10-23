# 实施计划

保留 tools/phase* 与旧 workflow 的封存哈希，在 tools/pr3-gates 新增包装器，.github/workflows/pr3-contracts.yml 新增只读权限 PR、master push、merge_group 及手动矩阵。checkout 默认 GitHub 合并 ref；记录 event head/base 并检查精确 parents。所有输出必须在 checkout 外新目录。

先建立真实子进程成功、失败、超时、工具缺失及证据缺失/损坏、零测试和不完整矩阵的 RED，再实现最小包装器。独立 clean commit 跑全部 11 项；组合 PR1、PR2 最终 HEAD 后重新跑相关门禁。任何源冲突先报告，不直接改历史规格。

PR27/28 固定 FFmpeg 下载以及 npm ci 可能需要网络；失败不能转为 skip。工作流不使用 pull_request_target、不使用私有凭据、不授予写权限。

组合提交只用于验证，不推送、发布或合并 PR。远端 CI 必须等用户批准精确 SHA 后再运行。

实现与组合宿主结果已记录在 tasks.md；新文档收尾只改变本规格，不改变已经测试的门禁代码。目标构建和远端 CI 仍单独待验收。

远端暴露 GitHub event base 可落后于实际生成的合并父节点。新增兼容路径仍以 GITHUB_SHA 和 refs/pull/N/merge 绑定实际输入，保留 eventDeclaredBase/actualMergeBase 与祖先证据，不从当前可变远端 ref 取新输入。真实 Git 回归先复现再实现；用完整 GitHub 事件变量做本地全矩阵重放，最终修复推送须新 SHA 批准。
