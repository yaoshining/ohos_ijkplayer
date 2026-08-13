# FFmpeg 8 OpenHarmony 动态库 SDK

本目录提供可供其他 HarmonyOS/OpenHarmony 工程复用的 FFmpeg 8.0 动态库 SDK 构建链。它不使用 Lycium、IJK 的 FFmpeg fork 或私有 patch，也不会生成或依赖 `libffmpeg.so`。支持 `arm64-v8a` 和 `x86_64`；仓库以 GitHub Actions 工作流 `.github/workflows/build-ffmpeg8.yml` 作为权威的最小交叉编译验证，成功运行会分别产出 `ffmpeg-8.0-ohos-arm64-v8a` 与 `ffmpeg-8.0-ohos-x86_64` artifact。

## 前置条件

- macOS 或 Linux 主机，已安装 `bash`、`curl`、`tar`、`make`、`shasum`。
- `OHOS_NDK` 指向 OpenHarmony NDK 根目录；该目录必须包含 LLVM 工具链与 sysroot。
- 若 NDK 布局不同，可用 `OHOS_LLVM_BIN` 和 `OHOS_SYSROOT` 显式指定路径。编译器使用不附加 API 后缀的 OpenHarmony target triple，API 能力由所选 NDK/sysroot 决定。

## 构建

```bash
export OHOS_NDK=/absolute/path/to/openharmony/ndk
./tools/ffmpeg8/build.sh                         # 默认 arm64-v8a
OHOS_ARCH=x86_64 ./tools/ffmpeg8/build.sh        # x86_64
```

可复现输入固定为上游 `ffmpeg-8.0.tar.xz` 与 SHA-256：

```text
b2751fccb6cc4c77708113cd78b561059b6fa904b24162fa0be2d60273d27b8e
```

脚本下载源码至 `out/ffmpeg8-work/downloads/`，每次重新解压并在独立工作目录中配置，因此不会修改仓库内旧的 `doc/FFmpeg/` 或播放器第三方目录。可使用以下变量改变工作目录或安装前缀：

```bash
FFMPEG8_WORK_DIR="$PWD/out/custom-ffmpeg8-work" \
FFMPEG8_PREFIX="$PWD/out/custom-ffmpeg8-sdk/x86_64" \
OHOS_ARCH=x86_64 JOBS=8 \
./tools/ffmpeg8/build.sh
```

- `OHOS_ARCH` 支持 `arm64-v8a`（默认）和 `x86_64`。
- 未显式设置 `FFMPEG8_PREFIX` 时，输出目录为 `out/ffmpeg8/$OHOS_ARCH/`。
- 若显式设置的 `FFMPEG8_WORK_DIR` 已存在，脚本仅会使用带有本脚本工作目录管理标记的目录；对未标记目录会直接失败，需调用方显式清理或改用新路径。
- 若显式设置的 `FFMPEG8_PREFIX` 已存在，脚本仅会清理带有本脚本 SDK 管理标记的旧输出；对未标记目录会直接失败，需调用方显式清理或改用新路径。

## 输出结构

默认 ARM64 输出为 `out/ffmpeg8/arm64-v8a/`，x86_64 输出为 `out/ffmpeg8/x86_64/`，两者结构相同：

```text
<architecture>/
  include/                       # FFmpeg 8 公共 C 头文件
  lib/
    libavcodec.so
    libavformat.so
    libavutil.so
    libavfilter.so
    libswscale.so
    libswresample.so
    pkgconfig/                   # libav*.pc、libsw*.pc
  licenses/FFmpeg-LGPL-2.1-or-later.txt
  VERSION                        # 版本、源码 URL、SHA-256、目标与 configure 参数
  configure-options.txt          # 每行一个完整 configure 参数
  PROTOCOLS.txt                  # configure 实际启用的 URL protocol 清单
  MANIFEST.tsv                   # 每个打包文件及字节大小
  ELF-REPORT.txt                 # ELF 架构、OS ABI、SONAME、DT_NEEDED 与大小
```

构建在安装前会断言 ABI 目标版本：`libavutil` 60.8.100、`libavcodec` 62.11.100、`libavformat` 62.3.100。版本不匹配会失败，而不会生成不兼容 SDK。

## 功能与许可证

构建保留 FFmpeg 标准组件边界和内置 demuxer、parser、解码器、字幕、滤镜、缩放与重采样能力，并启用 `http`、`https`、`tls`、`tcp`、`rtmp`、`rtp`、`udp` 等网络协议；不采用 IJK 的 `--disable-everything` 式裁剪。HTTPS/TLS 使用与 Samba 依赖闭包共同构建的 GnuTLS 3.8.7，并将 GnuTLS、Nettle、GMP、libtasn1 等完整静态链接进 `libavformat.so`，因此宿主无需额外部署 TLS 动态库。启用 `libsmbclient` 会链接 GPLv3 Samba 组件，因此 SDK 明确使用 GPLv3 发布，不能描述为纯 LGPL 制品。完整许可证随产物位于 `licenses/`，源码和配置可审计信息位于 `VERSION`。

## 验证

构建脚本最后自动调用校验，也可以对已产物单独执行：

```bash
export OHOS_NDK=/absolute/path/to/openharmony/ndk
./tools/ffmpeg8/verify.sh out/ffmpeg8/arm64-v8a
./tools/ffmpeg8/verify.sh out/ffmpeg8/x86_64
```

校验使用 NDK 的 `llvm-readelf`，对每个库要求 `ELF64`、与目标匹配的 `AArch64` 或 `X86-64` machine，并严格检查 SONAME 主版本（`avcodec` 62、`avformat` 62、`avutil` 60、`avfilter` 11、`swscale` 9、`swresample` 6）。`DT_NEEDED` 中的 FFmpeg SDK 依赖只能指向这六个已打包库；未知、缺失或未声明的 SDK 同级依赖会失败，NDK 平台系统库则不依赖脆弱的固定白名单。校验结果包含 `DT_NEEDED`、SONAME 和文件大小，并写入 `ELF-REPORT.txt`。

## 与旧 IJK 播放器的关系

本 SDK 是独立交付，不替换 `ijkplayer/src/main/cpp/third_party/ffmpeg`，也不修改播放器功能。旧 IJK 源码直接使用 `libavformat/url.h`、`URLContext`、`URLProtocol`、`ffurl_*` 和手工注册格式等 FFmpeg 私有/旧 API；这些 API 没有可直接链接标准 FFmpeg 8 动态库的一对一公开替代。后续播放器迁移应独立设计：以公共 `AVIOContext`/`avio_alloc_context()` 回调承载应用自定义 IO，并按需要重新实现缓存、异步读取和重连策略。

## SMB / libsmbclient（GPLv3）

此 SDK 使用 FFmpeg `n8.0` 提交 `140fd653aed8cad774f991ba083e2d01e86420c7`，上游 tarball 为 `https://ffmpeg.org/releases/ffmpeg-8.0.tar.xz`（SHA-256 `b2751fccb6cc4c77708113cd78b561059b6fa904b24162fa0be2d60273d27b8e`）。构建会锁定 Samba 4.20.7 提交 `3984b04d7085c428ab3126ef4cfac2a396b5b29e`，将 `libsmbclient.a` 和 zlib、popt、GMP、Nettle、libtasn1、GnuTLS 的静态闭包链接到 `libavformat.so`，因此 SDK 不需要 Samba 运行时 `.so`。

同一静态依赖闭包中的 GnuTLS 也作为 FFmpeg 的 TLS backend，构建与校验会同时门禁 `--enable-gnutls`、`https`/`tls` protocol、GnuTLS 字符串、动态依赖和未解析静态符号。

`patches/0001-libsmbclient-private-credentials.patch` 从 VidAll_Player 三项补丁移植到 FFmpeg 8.0。它仅给 `smb` URL protocol 私有上下文增加 `username`、`password` AVOption，并使用 `SMBCCTX` user-data/auth callback 读取它们；`workgroup`、`timeout` 行为保持不变。凭据不会写入 URL、HTTP header 或 FFmpeg 日志，也不修改 FFmpeg 公共 API。

该制品**不是 LGPL 制品**：启用 GPLv3 的 libsmbclient 后，FFmpeg 以 GPL 发布。`licenses/FFmpeg-LGPL-2.1-or-later.txt` 保留 FFmpeg 基础许可文本，`licenses/GPL-3.0-or-later.txt` 记录最终 GPL 义务。

构建命令（两个 ABI）：

```bash
export OHOS_NDK=/absolute/path/to/openharmony/ndk
./tools/ffmpeg8/build.sh
OHOS_ARCH=x86_64 ./tools/ffmpeg8/build.sh
```

ARM64 可供 VidAll_Player 使用的 prefix 为 `out/ffmpeg8/arm64-v8a/`；VidAll_TV 若需要 x86_64 模拟器则使用 `out/ffmpeg8/x86_64/`。每个目录的 `VERSION` 保存完整 configure 参数、源码 URL/tag/commit/SHA-256；`ELF-REPORT.txt` 保存 `llvm-readelf` 的 ELF/SONAME/DT_NEEDED 审计；`MANIFEST.tsv` 记录所有导出文件与大小。安装后 `.pc` 的 `prefix=${pcfiledir}/../..` 可随下游 staging 重定位。

本机构建自动执行补丁与 ELF/导出验证。可独立运行：

```bash
./tools/ffmpeg8/tests/test-sdk-contract.sh
./tools/ffmpeg8/tests/test-libsmbclient-patch.sh out/ffmpeg8-work/downloads/ffmpeg-8.0.tar.xz
FFMPEG8_SMB_TEST_CLIENT=/path/to/target-protocol-client \
  SMB_TEST_SERVER=host SMB_TEST_SHARE=media ./tools/ffmpeg8/tests/test-smb-service.sh
```

最后一项是针对真实 Samba 服务的目标端门禁：验证匿名、正确凭据、错误凭据及 URL/日志不泄漏密码。它要求调用方提供能向 FFmpeg `smb` protocol 传递 AVOption 的目标测试客户端；CI 不伪造该运行时证据。
