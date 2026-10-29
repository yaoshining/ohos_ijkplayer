# 证据身份与可访问边界

表中`docs/...`、`out/...`等未以斜杠开头的位置，绝对根目录统一为 `/Users/yaoshining/DevEcoStudioProjects/ohos_ijkplayer/`，不是当前独立clone的相对路径。`/private/tmp/...`已列完整绝对位置，仅是本机补充材料。全部绝对来源另见SOURCE-INVENTORY.json的source字段。

本轮只读核对已有材料，没有重跑测试、构建、设备或远端CI。以下本机原件不随文档提交；摘要使本机复核可追踪，但摘要本身不构成公开证据闭环。公开复核以README中的精确Git提交、仓库文件及Actions run为入口。若artifact过期，应保留缺口，不声称已重新下载。

| ID | 本机原件位置（非仓库链接） | SHA256 | 字节 |
|---|---|---|---|
| E1 | `out/phase23/ci-verification.json` | `8dc71a7e08f74f5a6ba48dc528560274a248a0004e979cbd95a369a30fdf2720` | 422 |
| E2 | `out/phase23/cleanup-final.json` | `418e73547d0e496568063892456634ee7b5e9c7e1be3bc87fbea15b8efbb169a` | 301 |
| E3 | `out/phase24/ci/verification.json` | `78c334c1a999919d38c0d572923624aedfe29b674d5e61f62ce848a709d330c2` | 420 |
| E4 | `out/phase26/ci/verification.json` | `712a803908bd1cc989d343c4bbc02a559f23ee0c0378a493129fd45590742c99` | 3992 |
| E5 | `out/phase27/ci/run-02-status.json` | `7aef5f254594ecf006205c15301c5c5dddf0863325a184eb041812ff891da846` | 1487 |
| E6 | `out/phase31-normal-validation-attempt01/SUMMARY.json` | `1b3117b7aead0c818122068907914acf8bf2bc7d8c3e4735e62ee8d365b73de4` | 2692 |
| E7 | `/private/tmp/phase28-parent-chain-ci-20261023/remote-ci/REPORT.md` | `3d0e8874fb36ee53124115ba1d9a5ebdb0432ef12e474e53c871131f6739406e` | 2961 |
| E8 | `/private/tmp/phase29-normal-terminal-remote-ci-20261023/REPORT.md` | `587b639a768eb0dbf94238099c90664cfaf1db3d629240ed69082ea667e990c0` | 2509 |
| E9 | `/private/tmp/phase30-remote-ci-20261023/REPORT.md` | `808f64039aab3ad2a595fd55c3f1264383e7b295ff6e5a2f4f0ce5ecff8ce05c` | 2430 |
| E10 | `/private/tmp/phase31-ci-remote-01/REPORT.md` | `ee1a20c30d9041dec2fbb98c0b3f56a41a4794c1f75794daadc3c5eb03339d83` | 2818 |
| E11 | `out/phase22/snapshots/03/ci-verification.json` | `4ff8eb9072cb7c57943a7575d68836199067f851a486b903960c5baea8074cb8` | 1710 |
| E12 | `out/phase22/DEVICE-CHECKLIST.md` | `c6e260182a003d7b663f7d49016b7bd3bc49b2f9424e19e69861be5a83b10864` | 1778 |

全部规格来源与可访问性见 SOURCE-INVENTORY.json。不得把本机路径拼成GitHub链接。
