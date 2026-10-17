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

## TV 当前组合的 OHCodec producer 入口

2026-10-17 起，本仓统一负责 FFmpeg/OHCodec 与 SMB/TLS 依赖生产。Player 仅消费固定 producer manifest 并生产 mpv/HAR/组合清单；TV 只集成统一组合和验收。本次 **Player、TV 全目录只读**，包含文档、来源锁与候选库。规则与执行记录见 `specs/001-ffmpeg-ohcodec-producer/`。

`build.sh` 保留普通 FFmpeg 多 ABI 构建；它不能替代以下 ARM64 OHCodec 基线入口。`producer-sdk.py` 使用固定 git 提交和三份摘要锁定补丁。原 `build-libsmbclient.sh` 仍是本仓的 SMB/TLS 源码生产入口；这次迁移使用八份已核对的历史缓存静态库，**没有重新构建全部静态依赖，fullyVerified=false**。

本机可重放命令（新输出目录，拒绝覆盖）：

```bash
python3 tools/ffmpeg8/producer-sdk.py import-baseline \
  --tv /Users/yaoshining/DevEcoStudioProjects/VidAll_TV \
  --delivery /Users/yaoshining/DevEcoStudioProjects/VidAll_Player/dist/ohcodec-diagnostics-20260923 \
  --output out/vidall-tv-baseline-sdk

python3 tools/ffmpeg8/producer-sdk.py build \
  --ndk /Applications/DevEco-Studio.app/Contents/sdk/default/openharmony/native \
  --smb /Users/yaoshining/.cache/vidall-player/smb-sysroot \
  --ffmpeg-repo /Users/yaoshining/.cache/vidall-player/libmpv-ohos-build/libmpv/ffmpeg \
  --builder-repo /Users/yaoshining/.cache/vidall-player/libmpv-ohos-build \
  --delivery /Users/yaoshining/DevEcoStudioProjects/VidAll_Player/dist/ohcodec-diagnostics-20260923 \
  --output out/vidall-tv-source-build --jobs 8
```

`import-baseline` 验证当前 TV HEAD/HAR/HAR 内 libmpv 和六库，逐项验证 delivery 证据，产出 `imported-baseline`。初始仅 `runtime-ready`，不能把旧缓存普通 FFmpeg headers 混入。

`build` 的输出 SDK 是 `OUTPUT/work/prefix`。记录 FFmpeg git archive、三份补丁、实际构建脚本、工具二进制、NDK sysroot、Clang resource headers、静态 archives/include/pkgconfig 的摘要；执行 ELF/SONAME/OHCodec 导出/SMB-TLS 依赖检查并逐库比较。原构建工具链的历史字节身份未知，当前工具链记录不能反向证明历史输入。

若编译安装已成功但后续打包检查失败，可用相同参数把 `build` 替换为 `package-build`，重新验证输入后只恢复打包；已有 manifest 的 SDK 拒绝重打包。恢复操作不等于再次源码编译。

完成构建后，可附加开发头文件和可重定位 pkgconfig 到导入包，必须明确它们来自本次 source-build，runtime 仍保持历史字节：

```bash
python3 tools/ffmpeg8/producer-sdk.py attach-headers \
  --sdk out/vidall-tv-baseline-sdk --manifest-sha256 IMPORTED_MANIFEST_SHA256 \
  --rebuilt-sdk out/vidall-tv-source-build/work/prefix \
  --rebuilt-manifest-sha256 REBUILT_MANIFEST_SHA256
```

此步骤会更新导入 manifest 和 handoff 摘要；消费方应在此完成后固定 `docs/vidall-tv-baseline-handoff.json` 给出的最终 manifest SHA256。不得用现场重算的摘要替代已经评审固定的值：

```bash
python3 tools/ffmpeg8/producer-sdk.py verify \
  --sdk SDK_ROOT --manifest-sha256 PINNED_MANIFEST_SHA256
```

manifest schemaVersion=1，字段与含义见 `specs/001-ffmpeg-ohcodec-producer/data-model.md` 和 `contracts/sdk.md`。路径均相对 SDK 根目录；manifest 是摘要入口，`files` 覆盖库、头文件、pkgconfig、许可证、SBOM 和证据。SBOM 是有缺口的库存清单，不能当作完整依赖来源认证。`producer.workingTreePatchSha256` 绑定 tools/ffmpeg8 和构建工作流范围内的已跟踪/未跟踪变更，不读取无关工作树或 keys；`buildRecipe` 另存实际用于源码构建的入口副本。

回归：

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tools/ffmpeg8/tests -p 'test_*.py' -v
bash tools/ffmpeg8/tests/test-sdk-contract.sh
bash tools/ffmpeg8/tests/test-ohcodec-patches.sh /path/to/ffmpeg-git-repo
```

以上为第一阶段入口。第二阶段已经替换 CI 为专用 OHCodec 源码流程并完成本机跨目录 clean 重复性；详细状态和剩余门禁见下节。所有产物设备验收仍为 `pending`。


## 第二阶段：重复性、源码闭包与专用 CI

最终结果与精确路径见 `docs/producer-reproducibility-report.md`。原 imported-baseline 保留；`out/vidall-tv-baseline-sdk-v2` 仅修正开发头文件为 FFmpeg 8.0，运行库仍为原 TV 六库。新 SDK 来自已固定 manifest 的旧包派生，基线提交未变；观察到 TV HEAD 新提交但全部媒体字节相同，单独记入 handoff。

三项已证明的构建身份污染：configure prefix 内嵌、父仓 Git 污染 FFMPEG_VERSION、AVCodec __FILE__ 绝对路径。`build-env.sh` 固定 `REVISION=8.0`/SOURCE_DATE_EPOCH，固定 configure prefix `/opt/ohos-ffmpeg8`，通过 build/src 相对 symlink 使源码路径稳定；安装使用 DESTDIR，随后移入 OUTPUT_ROOT/prefix。不会向 `/opt` 或历史 `/tmp` prefix 安装。

历史复现（不覆盖旧实验目录）：

```bash
OHOS_NDK=/Applications/DevEco-Studio.app/Contents/sdk/default/openharmony/native SMB_PREFIX=/Users/yaoshining/.cache/vidall-player/smb-sysroot FFMPEG_SOURCE_REPO=/Users/yaoshining/.cache/vidall-player/libmpv-ohos-build/libmpv/ffmpeg OUTPUT_ROOT="$PWD/out/history-replay-new" JOBS=8 bash tools/ffmpeg8/reproduce-history.sh
```

这里依赖与工具路径须与历史配置字符串一致。该受控实验把 __FILE__ 映射为历史路径，CFLAGS 映射记录在实际 config.mak；不修改源码逻辑。与本机 TV 六库全 SHA 相同的证据在 `out/producer-repro-investigation/reproducibility-v2-results.json`。

新来源构建：`dependency-sources.lock.json` 是**新的选择**，不是历史来源证明。`fetch-sources.py` 在下载和缓存命中时都验证 SHA；离线仅允许已有匹配缓存或本地 git archive，不能通过 --git-repo 绕过 release 离线约束。宿主 bison 是否源码构建单独记录，已有归档不等于实际使用；CI 显式 FFMPEG8_PIN_HOST_BISON=1。

```bash
OHOS_NDK=/path/to/native WORK_DIR="$PWD/out/new-deps/work" PREFIX="$PWD/out/new-deps/sysroot" SOURCE_CACHE="$PWD/out/new-deps/downloads" JOBS=8 FFMPEG8_PIN_HOST_BISON=1 bash tools/ffmpeg8/build-libsmbclient.sh
python3 tools/ffmpeg8/dependency-manifest.py --work out/new-deps/work   --sysroot out/new-deps/sysroot --cache out/new-deps/downloads --ndk /path/to/native
```

随后用 producer `build` 的 `--smb` 指向该 sysroot，增加 `--static-manifest` 和经核验的 `--static-manifest-sha256`。新清单绑定八库、headers、pkgconfig、源码选择、Samba 补丁、工具和许可证。新依赖的许可证另存 SDK 的 `licenses/source-dependencies`，不会仅留在外部 sysroot。单次源码构建默认 fullyVerified=false。第三阶段仅在绑定预锁、独立两次构建和固定宿主获取证据后，允许新选来源闭包 true；historicalSourceIdentityProven 始终独立为 false。

两次 clean 分别使用全新 OUTPUT；用 `compare-sdks.py --first SDK_A --second SDK_B --report report.json` 比较六库与开发文件。manifest 中工作目录/证据身份本来不同，不要求两个 manifest 字节相同。

CI 主入口 `ci-build-ohcodec.sh` 从公开锁定源码和本仓 baseline-evidence 启动，不读 Player/TV 或用户缓存。当前 Linux 工具链诊断 profile 固定公开 OpenHarmony 5.0 archive，**不是**本机 API24/6.1.1.115 的历史身份；实际云端运行结果见报告，不能把下载成功当编译/兼容性通过。无完整依赖/宿主工具锁时 `ci-gate.py` 失败，只有 diagnostics artifact 可保留，正式 artifact 不上传。不得添加 continue-on-error 绕过。

原 build.sh 仍可手动构建普通 SDK，但已从 OHCodec CI 门禁移除。Spec Kit 使用本仓官方 v1.2.1，见 `tools/speckit/README.md`。


## 第三阶段：独立静态构建与证据门禁

Linux CI 从 `ci-container.sh` 开始：Dockerfile 固定官方基础镜像摘要和 Debian 软件包快照，保存镜像/容器 identity、dpkg 版本、deb 摘要；容器里调用 `ci-build-ohcodec.sh`。仅已锁定的下载缓存可共享，两个依赖 source/work/sysroot 和两个 FFmpeg OUTPUT 独立新建。

本地实验先将 build-libsmbclient.sh、fetch-sources.py、dependency-sources.lock.json、dependency-paths.py、generator-lock.py 复制到新的 recipe 目录，设定 `LC_ALL=C TZ=UTC SOURCE_DATE_EPOCH=1755820644 PYTHONHASHSEED=1`，再执行以下入口。所有输出路径必须全新；下载缓存中的每项须已通过 fetch-sources.py 校验。

```bash
python3 tools/ffmpeg8/host-lock.py capture --ndk NDK --recipe RECIPE --profile macos-installed-API24 --output HOST_LOCK.json
python3 tools/ffmpeg8/run-dependency-build.py --root BUILD_A --recipe RECIPE --host-lock HOST_LOCK.json --cache DOWNLOADS --ndk NDK --jobs 6
python3 tools/ffmpeg8/run-dependency-build.py --root BUILD_B --recipe RECIPE --host-lock HOST_LOCK.json --cache DOWNLOADS --ndk NDK --jobs 6
python3 tools/ffmpeg8/dependency-repeat.py --first BUILD_A/sysroot --second BUILD_B/sysroot --require-build-records --report STATIC_REPEAT.json
```

为两侧运行 dependency-manifest.py 并显式传入 `--recipe RECIPE`，再运行 new-source-closure.py 生成新的证据包和 dependency-manifest-closed.json。Mac 已安装工具的获取来源仍未证明，因此仅能证明该 profile 下的重复性；不能因清单齐全就标记完整宿主获取验证通过。

受控 runner 不继承 OHOS_SYSROOT/OHOS_LLVM_BIN/OHOS_ARCH/HOSTCC/CFLAGS 等外部覆盖；从绑定的 NDK 与 ARM64 配置派生实际环境并记录。host-lock 在构建前后验证工具和 recipe；从源码构建的 bison/Heimdal 生成器在使用前冻结摘要，构建结束复核。

`ci-gate.py` 校验两个 SDK 的 manifest 外部固定摘要、重新比较实际库/头文件/pkgconfig、检查实际来源归档与闭包文档，不接受手写 allMatch/hostToolsVerified。`--verification-only` 允许成功报告新选来源验证，但正式产物仍需独立 release gate；当前 formalReleaseAllowed=false、历史工具链身份未证明、设备 pending，禁止正式发布或替换 TV 基线。

可重复性修复涉及默认路径：popt 的配置目录固定为 /etc；交叉 Samba/LDB 使用 configure 的安装路径，不再把临时源码树作为默认运行路径。这个行为改变没有真机验收。开发元数据可重定位不表示 SMB/媒体播放已通过。
