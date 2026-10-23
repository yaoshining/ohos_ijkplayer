# PR2 实际 CI 门禁

在 clean checkout 使用与 CI 相同入口：

```sh
python3 -B tools/pr2-gates/run.py --out /absolute/fresh/evidence-directory
```

CI 明确安装 Python 3.11 与 PyYAML 6.0.1。本机草稿预演使用 `--allow-dirty`，但 `GITHUB_ACTIONS=true` 时该参数必被拒绝。本机已使用 Python 3.10.9/PyYAML 6.0.1 实跑；版本不同如实记录，不把本机结果称为远端通过。

`commands.json` 是实际命令清单；每条 unittest 命令必须返回零且实际运行至少一个测试。非 unittest 的 SDK shell 合同独立按返回码判定。超时、命令失败、实际 HEAD 改变、文件字节改变、缺失或非法 artifact 均失败。输出目录必须在 checkout 外且首次不存在，只有校验后的 `artifact/` 可上传；收集失败只发布 runner 自身的失败 JSON。

PR 默认测试 GitHub 合并 checkout，身份校验实际 HEAD 的两个父提交与事件 base/head 完全一致；push/manual 校验 GITHUB_SHA；merge_group 还要求 base_sha 为实际可达祖先。身份不通过时仍留结构化失败证据。ignored 构建输出不进入源输入锁，所有 tracked 文件和未忽略文件前后字节仍要一致。

新增工作流覆盖 pull_request、master/交付分支 push、merge_group 与手工触发；对应工具、来源输入、workflow、本门禁与新规格路径变更触发检查。fork 使用只读权限和不持久凭据，不用 pull_request_target，不读 secrets。组合测试使用两个分支的独立入口，不能借用另一分支旧结果。

旧阶段封存和来源索引未改写；核对当前 Phase17/18/20 发布代码，没有绑定这四个旧 workflow 原字节的 source-index 条目。后续阶段的固定旧 workflow 由 PR3 保持原字节，本改动不涉及。正式产物仍 `formalArtifactAllowed=false`，既有目标工作流只保留诊断 artifact，不自动发布候选。

## TDD 与当前证据

初始 `red-01.log` 包含旧 workflow 缺失 PR/merge_group 与正式上传限制的语义失败；engine 尚不存在的用例属于缺失实现，不冒称行为失败。`review-red-02.log` 补复现错误 merge-group base、同 tree HEAD 漂移、CI dirty 预演、前置错误缺证、零用例误过与旧索引残留。之后 engine 最小修复通过。

第一次 full host 真实失败已保留：解释器被 shell 切换到缺 PyYAML 的 Homebrew Python；PR2 另外有需要 prepare 的源码测试缺环境。没有用玩具源码把它们改判为通过。第二次使用固定本机解释器，宿主范围全通过。摘要和各本机证据哈希见 [validation.json](../../specs/003-pr2-ci-gates/validation.json)。本机绝对目录仅为审查补充，公开复现依靠源码/命令和批准后的新 CI artifact。

未执行设备、长播或新目标构建；新 SHA 远端 CI、组合验证尚未完成。历史成功和本机预演不替代这些门禁。

## PR2 测试模块全集归属

每个模块都列入以下集合，自动化测试通过文件枚举核对并集完整、交集为空。宿主数量下降来自准备条件分离，不能据此声称目标全套已经运行。

|阶段|模块|宿主预演|目标准备后|
|---|---|---:|---|
|18|test_collect_paths.py|3|同模块再运行|
|18|test_evidence_contract.py|18|同模块再运行|
|18|test_host_isolation.py|3|同模块再运行|
|18|test_inputs.py|18|bootstrap展开的来源包测试|
|18|test_tool_inputs.py|2|同模块再运行|
|18|test_recipes.py|不运行|bootstrap后 out/phase18-ci/tests，4例|
|20|test_build_gate.py|3|prepare后全模块再运行|
|20|test_collect.py|2|同上|
|20|test_extract.py|2|同上|
|20|test_host_python_environment.py|1|同上|
|20|test_lifecycle.py|1|同上|
|20|test_runtime.py|18|同上|
|20|test_apply.py|不运行|prepare设置真实Samba/FFmpeg源码，2例|

PR2本门禁另25例。Phase18目标还运行展开的 integration/runtime测试、八个C/C++依赖、shaderc传递依赖、dovi/Rust宿主测试以及新十库的LP/mpv双目录构建；Phase20 native job运行真实Linux Samba/strace，target job完成两次全新目标构建和产物核验。它们未被宿主预演代替。

Phase20 的 `tee` 失败传播回归实际用退出7的子进程替换旧step左侧命令，执行 bash -e：冻结 a73e 父提交得到exit0，语义RED；当前step显式bash和 `set -euo pipefail` 后非零。此补充回归在第一次workflow最小修改后添加，通过冻结baseline证明旧问题，不冒称早于首次编辑。审查所涉四workflow只有该处shell管道，其他多行run不含未保护的tee管道。
