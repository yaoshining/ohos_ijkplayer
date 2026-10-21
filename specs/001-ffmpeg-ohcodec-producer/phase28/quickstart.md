# Phase28 验证入口

所有命令从 ohos_ijkplayer 仓库根运行；仅使用新 out/phase28 路径。当前以下实现/测试命令是计划入口，文件未生成前不可报告执行成功。

1. 边界：`python3 -B out/phase28/verify_boundary.py`，应确认三仓/12产物/候选/default 不变；另校验 phase27-precheck 对 snapshot02 的全量结果。
2. 真实函数 TDD：计划 `python3 -B out/phase28/tests/lifecycle/run.py --source baseline --out out/phase28/tests/lifecycle/red-01`，基线应出现指定顺序断言失败；编译失败不能算 RED。再以 `--source phase28` 和全新 green-01 目录检查修复。所有测试必须输出实际源摘要、compile/run 日志和 timeout 状态。
3. 编译：build-scope/design.md 中双根 FFmpeg/mpv 命令适配到 Phase28，必须在运行前冻结新源码和实验宏；原五库/libplacebo 不部署替换。
4. CI：新独立 checkout 干净重放后，展示精确 SHA 与文本清单申请推送；批准后才运行新 CI。错误日志和 source-index 必须始终收集。
5. 设备：deveco-cli 构建新独立诊断 HAP；安装/库/maps 绑定通过后，执行 contracts/validation.md。只使用应用保屏。测试结束读回 false、空计划、无进程。

失败路径不能由正常路径 PASS 抵消；GPU 完成未知实验必须被独立 watchdog 有界终止，不能将终止当作正常播放成功。
