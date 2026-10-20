# 验证入口

先运行python3 -B out/phase23/verify_boundary.py，只写Phase23复核记录。使用devecocli device list核对真实设备；所有build/run在out/phase23/app，运行明确--device <授权测试设备>。
Python使用PYTHONDONTWRITEBYTECODE=1、PYTHONNOUSERSITE=1及-B。保存RED、诊断、最小补丁、GREEN；实际命令随各轮日志存档。按照contracts/validation.md分别判定SMB、Vulkan与GL。新封存前再复核旧边界，旧证据不改。

本提交的可独立执行入口（需要 C/C++ 编译器、Python3、Node24）：

```sh
PYTHONDONTWRITEBYTECODE=1 PYTHONNOUSERSITE=1 python3 -B -m unittest discover -s tools/phase23/tests -v
PYTHONDONTWRITEBYTECODE=1 PYTHONNOUSERSITE=1 python3 -B -m unittest discover -s tools/phase23/diagnostic/tests -v
```

工作流 `.github/workflows/phase23-runtime-lifecycle.yml` 仅运行宿主源码合同，制品同时绑定 `tools/phase23` 和本规范目录。目标构建与设备结果在 `tools/phase23/evidence` 单独标记。设备/HAP/私有配置不随提交发布；`diagnostic/scenarios` 是历史实验源码，不作为新工程默认入口。
