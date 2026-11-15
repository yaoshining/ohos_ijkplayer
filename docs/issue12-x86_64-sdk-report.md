# Issue #12：x86_64 FFmpeg SDK 交付记录

## 已完成

- 在独立目录从 `32887363cb103163fe6557ca64c05539ad6d73f2` 构建 FFmpeg 8.0 与八个静态依赖。
- 实际主机 macOS arm64，Native SDK API26 / 26.0.0.105，Clang 15.0.4；本次为本机构建，不声称来自 CI。
- 六库 SONAME：avcodec 62、avformat 62、avfilter 11、avutil 60、swresample 6、swscale 9。ELF Machine 均为 x86_64。
- 提供匹配 include、可重定位 pkg-config；独立消费者经重定位后链接成功，启用 `--no-allow-shlib-undefined`，无链接警告或错误。
- 所需动态依赖均属于包内六库或当前 OHOS NDK x86_64 平台库；八个静态 archive 的全部 ELF 对象架构通过核验。
- 来源锁、configure 配置、工具摘要、完整 sysroot/Clang resource 摘要、许可证、SPDX SBOM、每文件摘要随包交付。解包后的 309 项 SHA256SUMS 验证通过。
- Todoist 使用一个会话分组、12 项可勾选任务（含 PR 合并收尾）；会话规范写入 AGENT.md，并由 AGENTS.md 引用。

## 未完成

目标设备/模拟器运行、HTTPS/SMB 服务端运行测试、较低 API 兼容性、两次 clean 字节重复性均未执行。manifest 明确保留 `fullyVerified=false` 和 `deviceAcceptanceStatus=pending`。Player/HAR/TV 消费端接入属于后续工作。

## 卡在哪

构建与主机验证没有剩余阻塞；目标端验收尚无本次执行证据。

## 接下来做什么

消费端固定下载包 SHA-256 和 manifest SHA-256，验证后按软件解码合同编译。此 SDK 不导出 `av_ohcodec_*`，必须禁用依赖该接口的 OHCodec 编译分支；没有关闭恢复 stub。HTTPS/TLS/SMB 已编译启用，运行结果仍为 pending。

### 交付文件和校验

SDK：`ffmpeg8-ohos-x86_64-20261115-r2.tar.gz`（约 17 MB）。

```text
SDK SHA-256: 3b3e7763e381a569e8362cd4d828e9c3a89605b7505de6f04b14fb46c870e269
manifest.json SHA-256: b74fd1c9afc9adbfa766849bc7c494cc4511684d84f79b0649ad2f3b3146634a
配套源码包 SHA-256: a09f29c170841c9129cab9e92c158f90e30de71151288571088da4ce77992200
```

源码包 `ffmpeg8-ohos-x86_64-sources-20261115.tar.gz`（约 89 MB）包含已锁定的源码归档与构建配方。SDK 中 `evidence/recipe` 保存构建脚本；`evidence/package-x86-sdk.py` 和 `evidence/audit-x86-sdk.py` 保存本次审计打包入口。SBOM 作为依赖库存，不冒充设备验证或完整供应链认证。

下载 `.sha256` 文件与 SDK 后：

```sh
shasum -a 256 -c ffmpeg8-ohos-x86_64-20261115-r2.tar.gz.sha256
tar -xzf ffmpeg8-ohos-x86_64-20261115-r2.tar.gz
cd ffmpeg8-ohos-x86_64-20261115-r2
shasum -a 256 -c SHA256SUMS
```

可重放构建：在固定提交的独立源码目录设置 `OHOS_NDK`，执行 `OHOS_ARCH=x86_64 JOBS=8 bash tools/ffmpeg8/build.sh`。审计打包入口使用 `--checkout`、`--ndk` 和全新 `--output`，见 `--help`。当前配方按校验过的来源 URL 下载输入；配套源码包用于保存对应输入。

## 离目标还差多少

SDK 已公开发布：https://github.com/yaoshining/ohos_ijkplayer/releases/tag/ffmpeg8-x86_64-sdk-20261115 。四个附件重新下载后，两包 SHA-256 与固定值一致；SDK 解包后的 309 项摘要通过。#12 七项交付要求已完成并关闭，Todoist 已整合为一个会话分组，原 11/11 项完成，新增 T12 跟踪 PR 合并。

最初上传曾被自动审批拒绝；用户随后明确允许公开发布这些交付文件，本次上传已获授权并成功执行。目标运行等缺口仍保持未验证。协作规范与审计工具保存在独立分支 `codex/issue12-x86_64-sdk`，不声称已合并 master。

## PR #13 评审修正

- 增加 pkg-config 的 libdir、includedir、exec_prefix 可重定位检查；复制 SDK 后重新执行完整审计，拒绝指向原目录的绝对库链接。
- SPDX 文档增加 documentDescribes 与 DESCRIBES 关系，并校验其与包 ID 一一对应。r2 在相同已编译六库上重新打包，仅修订审计证据和元数据；原始发布文件保留，配套源码包不变。
- CI 下载 Popt 时原站证书链校验失败，切换 MacPorts 镜像，源码 SHA-256 仍为 c25a4838fc8e4c1c8aacb8bd620edb3084a3d63bf8987fdad3ca2758c63240f9；同步 producer 输入锁摘要，TLS 校验保持开启。该修正不改写本次 SDK 的历史构建来源记录。
- AGENT.md 同步“每个会话一个分组”及加粗状态标签、关键词的汇报样式。
