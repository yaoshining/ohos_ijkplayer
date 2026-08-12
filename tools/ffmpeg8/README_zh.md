# FFmpeg 8 OpenHarmony 动态库 SDK

本目录提供可供其他 HarmonyOS/OpenHarmony 工程复用的 FFmpeg 8.0 ARM64 动态库 SDK 构建链。它不使用 Lycium、IJK 的 FFmpeg fork 或私有 patch，也不会生成或依赖 `libffmpeg.so`。仓库以 GitHub Actions 工作流 `.github/workflows/build-ffmpeg8.yml` 作为权威的最小交叉编译验证：成功运行会产出 `ffmpeg-8.0-ohos-arm64-v8a` artifact。

## 前置条件

- macOS 或 Linux 主机，已安装 `bash`、`curl`、`tar`、`make`、`shasum`。
- `OHOS_NDK` 指向 OpenHarmony NDK 根目录；该目录必须包含 LLVM 工具链与 sysroot。
- 默认 API Level 为 12。以 `OHOS_API_LEVEL=<level>` 覆盖；若 NDK 布局不同，可用 `OHOS_LLVM_BIN` 和 `OHOS_SYSROOT` 显式指定路径。

## 构建

```bash
export OHOS_NDK=/absolute/path/to/openharmony/ndk
./tools/ffmpeg8/build.sh
```

可复现输入固定为上游 `ffmpeg-8.0.tar.xz` 与 SHA-256：

```text
b2751fccb6cc4c77708113cd78b561059b6fa904b24162fa0be2d60273d27b8e
```

脚本下载源码至 `out/ffmpeg8-work/downloads/`，每次重新解压并在独立工作目录中配置，因此不会修改仓库内旧的 `doc/FFmpeg/` 或播放器第三方目录。可使用以下变量改变工作目录或安装前缀：

```bash
FFMPEG8_WORK_DIR=/tmp/ffmpeg8-work \
FFMPEG8_PREFIX=/tmp/ffmpeg8-sdk/arm64-v8a \
OHOS_API_LEVEL=12 JOBS=8 \
./tools/ffmpeg8/build.sh
```

## 输出结构

默认输出为 `out/ffmpeg8/arm64-v8a/`：

```text
arm64-v8a/
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
  MANIFEST.tsv                   # 每个打包文件及字节大小
  ELF-REPORT.txt                 # ELF 架构、OS ABI、SONAME、DT_NEEDED 与大小
```

构建在安装前会断言 ABI 目标版本：`libavutil` 60.8.100、`libavcodec` 62.11.100、`libavformat` 62.3.100。版本不匹配会失败，而不会生成不兼容 SDK。

## 功能与许可证

构建保留 FFmpeg 标准组件边界和内置网络、协议、demuxer、parser、解码器、字幕、滤镜、缩放与重采样能力；不采用 IJK 的 `--disable-everything` 式裁剪。外部 GPL/nonfree 编解码器不启用，因此 SDK 使用 FFmpeg LGPL v2.1-or-later 许可条款。完整许可证随产物位于 `licenses/`，源码和配置可审计信息位于 `VERSION`。

## 验证

构建脚本最后自动调用校验，也可以对已产物单独执行：

```bash
export OHOS_NDK=/absolute/path/to/openharmony/ndk
./tools/ffmpeg8/verify.sh out/ffmpeg8/arm64-v8a
```

校验使用 NDK 的 `llvm-readelf`，对每个库要求 `ELF64`、`AArch64` 与存在 SONAME，并将 `DT_NEEDED`、SONAME 和文件大小写入 `ELF-REPORT.txt`。这可作为发布前的 ARM64 OpenHarmony ELF 记录。

## 与旧 IJK 播放器的关系

本 SDK 是独立交付，不替换 `ijkplayer/src/main/cpp/third_party/ffmpeg`，也不修改播放器功能。旧 IJK 源码直接使用 `libavformat/url.h`、`URLContext`、`URLProtocol`、`ffurl_*` 和手工注册格式等 FFmpeg 私有/旧 API；这些 API 没有可直接链接标准 FFmpeg 8 动态库的一对一公开替代。后续播放器迁移应独立设计：以公共 `AVIOContext`/`avio_alloc_context()` 回调承载应用自定义 IO，并按需要重新实现缓存、异步读取和重连策略。
