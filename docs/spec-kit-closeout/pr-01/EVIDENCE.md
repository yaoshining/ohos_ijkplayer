# 证据身份与可访问边界

表中`docs/...`、`out/...`等未以斜杠开头的位置，绝对根目录统一为 `/Users/yaoshining/DevEcoStudioProjects/ohos_ijkplayer/`，不是当前独立clone的相对路径。`/private/tmp/...`已列完整绝对位置，仅是本机补充材料。全部绝对来源另见SOURCE-INVENTORY.json的source字段。

本轮只读核对已有材料，没有重跑测试、构建、设备或远端CI。以下本机原件不随文档提交；摘要使本机复核可追踪，但摘要本身不构成公开证据闭环。公开复核以README中的精确Git提交、仓库文件及Actions run为入口。若artifact过期，应保留缺口，不声称已重新下载。

| ID | 本机原件位置（非仓库链接） | SHA256 | 字节 |
|---|---|---|---|
| E1 | `docs/producer-phase8-report.md` | `22650f64c997049b357b3a56ce16a052b0439e632b28adc30569d3eede7c9334` | 10611 |
| E2 | `out/phase8/ci-independent-verification.json` | `06b5e99c0125ff686ad4f6228bc6b6d5900fb0ccd904aa3be8de482e6df84de9` | 1226 |
| E3 | `out/phase10/resume-01/handoff.json` | `5262a06d3669388a735d58f2cf4ac97ead7ed33d4d62517cd0fd852b20958a24` | 3151 |
| E4 | `out/phase10/resume-01/ci-verification.json` | `7fe474c827d2e5e3d69b07b941c57e5048bb81e31d43186acf2ec285c49844b6` | 82876 |
| E5 | `out/phase17/completion-review.json` | `40529958bdc691aae3da19854ac6d47ceccc3640d4e20f570e297922ce3cfa6b` | 806 |
| E6 | `out/phase17/ci/published-final-commit-verification.json` | `d555dc29cfa32f8602cca1134a27012ed6a13ae17c53826c332418f2f68042bb` | 247 |
| E7 | `out/phase17/ci/fourth-run-artifact-verification.json` | `fcfc29ed976700d015c99aed8bb377c2871b05c36b98dcdcc8b86361fdc73e17` | 3000 |

全部规格来源与可访问性见 SOURCE-INVENTORY.json。不得把本机路径拼成GitHub链接。
