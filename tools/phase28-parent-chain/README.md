# Phase28 完整父级链宿主 CI

该目录是已审查 resume-04 R1/R2/F1 的自包含文本验证包。运行：

```sh
python3 -B tools/phase28-parent-chain/runner.py --out /tmp/phase28-parent-chain-new-run
```

依赖 Python 3.10+ 和 clang/pthread（父链启用 ASan/UBSan）。无安装步骤、无运行时网络、无设备操作。Linux GitHub runner 与本地 macOS 结果分别记录；本地通过不是远端通过。

验证包括真实父级 RED 5、GREEN 12、独立完整源码 queue 变异拒绝、FFmpeg 回调两种宏各 8、11 个合成清理场景和 9 项 CI 门禁测试。外部平台 API 仍由 harness stub；精确抽取记录源 SHA/函数 SHA，不声称完整产品运行。

`provenance.json` 对每份导入文件绑定 producer 中的相对原路径及 SHA；`source-index.json` 覆盖本目录全部文本输入。mpv GPL/LGPL、FFmpeg GPL/LGPL 原文保留于 licenses。源子集和诊断补丁继承源文件许可证，不声称整产品已取得额外许可或完成来源闭包。

仅 artifact/ 中允许列表 UTF-8 JSON/log 上传，保留所有运行失败日志与退出码，索引不递归包含自身。不会上传编译出的 harness、源码副本、HAP、库、SDK、签名、凭据或私人媒体/设备日志。

formalArtifactAllowed=false。产品 normal UNSAFE 策略、真实 GPU 永久挂起、强并发、物理 HDR/主观声画继续待验收。新远端 CI 等精确 SHA 批准后才执行。

默认拒绝脏工作树和 checkout 内输出；`--allow-dirty` 仅用于开发重放，并显式标记 exactCommitReplay=false。最终证据必须来自干净精确提交，前后 HEAD/status、输入索引和 workflow 摘要相同。允许文本单文件 16 MiB、总量 128 MiB，超限/非文本关键日志使任务失败。
