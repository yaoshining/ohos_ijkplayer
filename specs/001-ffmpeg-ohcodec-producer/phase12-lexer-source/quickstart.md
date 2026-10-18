# Phase12 实物复验

从 producer 根目录执行：

```sh
PYTHONDONTWRITEBYTECODE=1 python3 -B -m unittest discover -s tools/lexer-source-profile/tests -v
PYTHONDONTWRITEBYTECODE=1 python3 -B tools/lexer-source-profile/profile.py out/phase12/generation-controls/apple-fresh/gate-record.json --require-match
PYTHONDONTWRITEBYTECODE=1 python3 -B -m unittest discover -s tools/ffmpeg8/tests -p test_python_target_paths.py -v
```

期望新门禁21项、Python8项通过；实际记录门禁 sourceOutputMatches=true，historicalInstallationProven=false。实际记录包含本机绝对路径，仅在输入均保留时可复验；CI用合成夹具验证拒绝行为，没有运行本轮Linux生成器/全链构建。

真实工具构建、两次生成/目标编译、归档/链接对照和失败记录见 out/phase12；原脚本输出目录必须是全新目录，不覆盖封存结果。所有make包括dry-run禁止在旧树执行。完整报告 docs/producer-phase12-report.md。

最终边界先核验旧Phase11索引、当前TV和候选/默认inventory，再核验本轮evidence-index；不要直接运行会写回旧证据目录的脚本。设备pending、formalArtifactAllowed=false。
