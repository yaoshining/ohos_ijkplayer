# PR1 实际 CI 门禁

在 clean checkout 使用与 CI 相同入口：

```sh
python3 -B tools/pr1-gates/run.py --out /absolute/fresh/evidence-directory
```

CI 明确安装 Python 3.11 与 PyYAML 6.0.1。本机草稿预演使用 `--allow-dirty`，但 `GITHUB_ACTIONS=true` 时该参数必被拒绝。本机已使用 Python 3.10.9/PyYAML 6.0.1 实跑；版本不同如实记录，不把本机结果称为远端通过。

`commands.json` 是实际命令清单；每条 unittest 命令必须返回零且实际运行至少一个测试。非 unittest 的 SDK shell 合同独立按返回码判定。超时、命令失败、实际 HEAD 改变、文件字节改变、缺失或非法 artifact 均失败。输出目录必须在 checkout 外且首次不存在，只有校验后的 `artifact/` 可上传；收集失败只发布 runner 自身的失败 JSON。

PR 默认测试 GitHub 合并 checkout，身份校验实际 HEAD 的两个父提交与事件 base/head 完全一致；push/manual 校验 GITHUB_SHA；merge_group 还要求 base_sha 为实际可达祖先。身份不通过时仍留结构化失败证据。ignored 构建输出不进入源输入锁，所有 tracked 文件和未忽略文件前后字节仍要一致。

新增工作流覆盖 pull_request、master/交付分支 push、merge_group 与手工触发；对应工具、来源输入、workflow、本门禁与新规格路径变更触发检查。fork 使用只读权限和不持久凭据，不用 pull_request_target，不读 secrets。组合测试使用两个分支的独立入口，不能借用另一分支旧结果。

旧阶段封存和来源索引未改写；核对当前 Phase17/18/20 发布代码，没有绑定这四个旧 workflow 原字节的 source-index 条目。后续阶段的固定旧 workflow 由 PR3 保持原字节，本改动不涉及。正式产物仍 `formalArtifactAllowed=false`，既有目标工作流只保留诊断 artifact，不自动发布候选。

## TDD 与当前证据

初始 `red-01.log` 包含旧 workflow 缺失 PR/merge_group 与正式上传限制的语义失败；engine 尚不存在的用例属于缺失实现，不冒称行为失败。`review-red-02.log` 补复现错误 merge-group base、同 tree HEAD 漂移、CI dirty 预演、前置错误缺证、零用例误过与旧索引残留。之后 engine 最小修复通过。

第一次 full host 真实失败已保留：解释器被 shell 切换到缺 PyYAML 的 Homebrew Python；PR2 另外有需要 prepare 的源码测试缺环境。没有用玩具源码把它们改判为通过。第二次使用固定本机解释器，宿主范围全通过。摘要和各本机证据哈希见 [validation.json](../../specs/002-pr1-ci-gates/validation.json)。本机绝对目录仅为审查补充，公开复现依靠源码/命令和批准后的新 CI artifact。

未执行设备、长播或新目标构建；新 SHA 远端 CI、组合验证尚未完成。历史成功和本机预演不替代这些门禁。

## PR1 范围

|实际宿主命令组|预演用例数|目标承接|
|---|---:|---|
|门禁真实执行及失败边界|23|本门禁|
|FFmpeg producer|138|build-ffmpeg8.yml source-producer真实源码双clean|
|HX509合同|21|完整180分钟历史诊断只保留显式opt-in|
|cross-root|2|普通源码/配置合同|
|lexer|21|普通源码/配置合同|
|Phase17合同|25|phase17-mpv-repro.yml bootstrap和双目录交叉构建|
|Phase17 repeat|23|同上|
|SDK shell合同|实际退出0|单独shell测试，不计unittest数量|

不要求恢复历史 lexer 哈希或重启暂停的 parser/sanitizer。HX509长构建不是合并前置；相关普通宿主正常/边界/失败回归仍为门禁。source-producer 和 Phase17 目标构建需各自新 SHA/实际 merge 证据。
