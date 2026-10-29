# 分层重放

宿主CI工具包：`python3 -B tools/phase29-normal-terminal/runner.py --out /tmp/phase29-exact`。输出必须在checkout外；默认要求clean。`--allow-dirty`仅开发排错，不能作为精确提交证据。脚本安装锁定TypeScript4.9.5到输出目录并测试实际ArkTS方法；不运行目标构建或设备。

本机目标构建的完整argv见本地 `evidence/target-api-04/commands.json` 与 `evidence/build-normal-e.log`、`build-normal-f.log`。需要此前已封存完整输入包、API24 SDK、静态依赖及已授权签名，本文本包不含这些二进制。

设备仅独立诊断bundle，按 `device/run.py` 的场景白名单执行；原始日志本地私有保存，不上传CI。
