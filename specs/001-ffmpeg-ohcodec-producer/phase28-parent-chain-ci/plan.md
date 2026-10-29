# 实施计划

基于已推送 b905b49b65d5caa74a0e2893fec00c9aad38b22d 的独立 checkout；不混入 producer 主仓脏改动。复用已审查源文件和测试，不修改产品算法。

先写 CI 接受/上传门禁回归并实际 RED，再实现最小 runner、执行 GREEN。输入固定于 tools/phase28-parent-chain，source-index 覆盖其全部文本文件（不自包含）。工作输出在独立目录，子程序完整日志与退出码受控记录。外部 queue 变异输入不覆盖固定输入。

新增独立 workflow，只监听新目录/规格/本身，contents:read，无设备、凭据或部署。旧 phase28 workflow 路径不匹配本提交，不触发旧验证。保留当前已有 workflow 和历史失败证据。

本地精确提交重放 → root 独立审查 → 用户批准 SHA → 推送 → 核对 run.head_sha、结论、artifact digest 和解包索引。任何阶段失败均保持失败原记录，不减弱验收条件。来源仅为审查所需子集，不声称本 CI 完成完整产品来源闭包或 ARM64 目标构建。
