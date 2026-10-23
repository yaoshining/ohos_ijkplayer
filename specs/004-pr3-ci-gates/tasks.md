# 任务

- [x] G001 新增 spec/plan 和范围声明。
- [x] G002 先建立缺失实现 RED（/private/tmp/pr3-red.log），实现真实子进程及证据门禁后 11 项 GREEN（/private/tmp/pr3-green.log）；本机路径仅审查补充，不充当远端永久证据。
- [x] G003 新增 PR 矩阵及失败聚合门禁，旧封存不改。
- [ ] G004 最终精确 clean commit 运行完整 11 项及审查（候选 2434ea4 已 11/11；随后聚合修复须新 SHA 重放）。
- [ ] G005 合并 PR1/PR2/PR3 精确输入的临时组合验证。
- [ ] G006 提供精确 SHA 预览，批准后推送并核对远端 CI。

目标设备、物理 HDR/主观声画、真实 GPU 永不返回和任意强并发未在本轮验证，继续待验收。60 分钟长播不是接入前置条件，本轮不运行。

复审补充：真实临时 Git 仓库与 PR/merge_group/manual 身份、浅克隆限制、真实 11 artifact CLI 聚合、第二/末项损坏负例均纳入回归。先前聚合提前返回的语义 RED 已保留在本机 /private/tmp/pr3-aggregate-red.log；修复后 GREEN 18 项。远端权威证据仍待批准推送。
