# 重放与交付核验

在仓库根目录，先运行固定脚本：

```sh
SPECIFY_FEATURE_DIRECTORY=specs/001-ffmpeg-ohcodec-producer/phase30-close-recovery SPECIFY_FEATURE_NO_PERSIST=1 bash .specify/scripts/bash/check-prerequisites.sh --json --require-spec --require-tasks --include-tasks
python3 -B tools/ffmpeg8/phase30-close-recovery/test_recovery.py
```

宿主需 Python 3、clang、patch、pthread。预期原版 Stop/Destroy 的第二次创建失败，候选两次成功；原版与候选各 8 项用例均符合各自断言。故意保留资源关闭 leak 检测，仍启用 ASan/UBSan，不能宣称无内存保留。

正常构建命令见 `tools/ffmpeg8/phase30-close-recovery/README.md` 的“正常构建入口”。必须准备全量 9921 文件的 Phase30 A 源码、固定静态依赖与 OpenHarmony NDK；仓库宿主测试不需要这些本地封存路径，也不等于可从网络自动重建整个 SDK。

真机日志见同目录 `evidence/`，截图摘要由交付记录绑定。音频依据 getMaxAmplitudeForOutputDevice；不是远程主观听音。最终交付校验 SDK manifest 的全部文件、归档 SHA256 和合并树的产品文件一致性。

PR 与 master push 的新工作流仅运行宿主回归、规格 prerequisite；既有完整宿主门禁保持。等待所有必需检查成功及阻塞评审解决，再通过 PR 合并；不使用管理员绕过门禁。
