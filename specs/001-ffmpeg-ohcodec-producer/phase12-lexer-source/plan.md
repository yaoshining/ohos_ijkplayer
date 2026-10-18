# Phase12 最小实施计划：剩余 lexer 来源

2026-10-18。业务分支 `yaoshining-hdr-playback` 保持；诊断增量拟沿用 `codex/hx509-history-diagnostics`。输入：[spec.md](spec.md)。按主会话20:15直接人类授权继续实现来源诊断；14:35先确认方案的消息早于该授权。运行目录 API 不在本轮实现范围。

## 范围与技术上下文

使用 Python 3 标准库、unittest、现有固定 Bison/Flex/M4 与目标 clang；宿主 macOS/Linux 分别验证，目标为现有 OHOS ARM64 诊断工具链。文件/JSON 保存来源与产物证据，无服务、数据库或产品接口。目标是来源可复核和原始字节对比，不设置无关性能指标。

HX509 profile 已有源码与双平台证据，直接复用。新增内部诊断目录 `tools/lexer-source-profile/`（尚未创建），仅解决另一个 `lex.lex.c.124.o` 的生成器来源。初始改动限来源记录校验器、scanner 特征检测和回归；只有找到可追溯候选，才增加隔离生成/编译入口。默认生成器、现有 recipe/来源锁、SDK 指针均保持。

## 执行顺序与验证门槛

1. 复核封存索引和基线；新结果仅写 `out/phase12`。需改已封存文件时先保存原字节与映射。
2. 固定公开归档/完整提交/原补丁及 SHA，整理排除矩阵。版本号、个别特征吻合只算候选，不等于来源确认。
3. 新检测器先真实 RED，再最小实现 GREEN：缺失来源、摘要漂移、错误版本伪阳性和已知三组 scanner 特征均覆盖。
4. 有来源候选才实际重建工具；固定 M4/骨架、lex.l/parse.y、环境和 Waf 编码行为，分别比较 stdout 与落盘 C/H。
5. 以固定目标编译器、头文件、宏及 flags 编译，比较完整对象 SHA/节/符号/重定位。C 不匹配时编译仅作为排除对照，不提升来源匹配状态。不得手改生成 C 或用历史对象补入归档。
6. 对象匹配后才做归档成员 occurrence/顺序与重链接控制，记录 link map、stdin GOT、最终 avformat SHA。保留 Python 修复意味着不以完整 TV SHA 相等作为成功条件。
7. 按实际代码/配方变更运行针对性回归和 CI；双 fresh 仅用于发生变更的生成/构建链。来源不匹配则交付具体排除结果，不为凑结果重跑未变全链。

## 宪章检查

设计前与设计后：三仓职责、当前 TV 基线、来源闭包与设备边界均符合；本轮实物边界见 `out/phase12/solution-review-boundary.json`，24,224 项通过。TDD 属后续实现门槛，当前未声称 RED/GREEN 已执行。运行目录 API、消费端接线、设备和已暂停的 parser 故障注入/sanitizer 均不纳入本轮实现。

## 工件与未决结果

本目录包含 spec、plan、research、data-model、quickstart；内部构建诊断没有新增外部契约，省略 contracts。tasks/analyze/implement 依序执行。精确 Flex 来源尚未确认，这是实验结果缺口；设计已规定未找到时的可验收输出，不以猜测填补。运行目录另见 `docs/producer-remaining-solution-review.md`，只复核既有方案。

官方 setup-plan 已运行，输出在 `out/phase12/setup-plan.json`；没有切换 `.specify/feature.json`。规划前后均无 extensions.yml，无需执行扩展 hooks。没有宪章例外。
