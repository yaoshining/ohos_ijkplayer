# PR2 CI门禁范围

依据2026-10-24明确授权：补齐PR/未来组合验证，不修改旧封存、原工作树或TV，不推送新SHA直到精确批准。不运行设备或长播，不替换候选。formalArtifactAllowed=false。

- FR01 PR事件使用实际合并checkout，记录HEAD、父提交与事件head/base；不能记录PR head却测merge。push/manual/merge_group也绑定实际checkout。
- FR02 实际执行宿主源码/配置/正常边界失败回归，任何子进程失败/timeout/输入漂移非零退出。日志收集成功不得覆盖测试失败。
- FR03 输入锁覆盖所测仓库所有tracked文件的实际字节；开始/结束一致，精确重放要求clean。允许脏预演必须显式且不记精确通过。
- FR04 失败仍收集限定文本日志、身份、结果索引，拒绝越界/符号链接/二进制/缺失必要文件；诊断目标制品沿用既有独立范围，禁止正式自动发布。
- FR05 fork PR不读secrets、不用pull_request_target，不持久checkout凭据，最小contents:read。
- FR06 workflow/gate/spec/来源锁变更均纳入对应PR门禁。merge_group不靠PR路径过滤猜测放行。正常目标构建不能被仅宿主通过替代。
- FR07 各阶段历史CI不冒充新SHA/组合CI；当前远端run仅观察，不取消或重启。

PR2宿主覆盖Phase18来源/工具/证据契约与Phase20实际C运行目录生命周期；Phase18新十库+LP/mpv、Phase20真实Linux Samba及目标两fresh分别保留真实执行，宿主不能替代。

## 真实 CI 发现的输出目录边界

Phase20 native run `39995316236` 的实际 Samba 测试通过，但快照将未忽略的生成文件当作源输入，收尾失败。FR03 的最小落地补充：仅允许 `/out/phase18-host/`、`/out/phase18-ci/`、`/out/phase18-artifact/`、`/out/phase20-ci/`、`/out/phase20-artifact-native/`、`/out/phase20-artifact-target/` 六个精确输出根。由 Git ignore 处理新生成文件，不改变 engine 比较逻辑；任何已 tracked 文件（即使位于这些根）、其他未忽略文件、原输入删改仍拒绝。旧失败不能改判为成功，新修复 SHA 仍需独立远端验证。

组合范围说明：PR1既有 `/out/` 忽略规则保持原样。PR2精确六根块置顶以避免同尾冲突；组合仍继承PR1旧策略，不能宣称组合拒绝所有未知out文件。仓库根未忽略文件与全部tracked字节仍在门禁范围。
