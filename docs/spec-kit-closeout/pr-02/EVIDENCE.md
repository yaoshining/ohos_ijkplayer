# 证据身份与可访问边界

表中`docs/...`、`out/...`等未以斜杠开头的位置，绝对根目录统一为 `/Users/yaoshining/DevEcoStudioProjects/ohos_ijkplayer/`，不是当前独立clone的相对路径。`/private/tmp/...`已列完整绝对位置，仅是本机补充材料。全部绝对来源另见SOURCE-INVENTORY.json的source字段。

本轮只读核对已有材料，没有重跑测试、构建、设备或远端CI。以下本机原件不随文档提交；摘要使本机复核可追踪，但摘要本身不构成公开证据闭环。公开复核以README中的精确Git提交、仓库文件及Actions run为入口。若artifact过期，应保留缺口，不声称已重新下载。

| ID | 本机原件位置（非仓库链接） | SHA256 | 字节 |
|---|---|---|---|
| E1 | `out/phase18/handoff.json` | `5ff5fd86956ac59f7ece26744db2aeaf8ce7e9292eff0938421d8b3833fad11c` | 2305 |
| E2 | `out/phase19/handoff.json` | `607eeab869b1afd744eef1fbb4f0aa8f0fe786199ffff0ed1de297eba1927afc` | 2687 |
| E3 | `out/phase20/handoff.json` | `af2a3da4dbcaa13c0920dbdbb0824ba900d5ce1854ee67a8762b287b35fa3446` | 1053 |
| E4 | `out/phase20/root-independent-local-v3-verification.json` | `3d14b0b0f4ba802e7fa2c79c788013dee16f91807dfeb53aebac614eff231332` | 503 |
| E5 | `out/phase20/root-independent-target-verification.json` | `d8f393bff48fb31ac763c0d5413b9b97cd79ce7953b25f780be6b2f6d3021ce4` | 287 |

全部规格来源与可访问性见 SOURCE-INVENTORY.json。不得把本机路径拼成GitHub链接。
