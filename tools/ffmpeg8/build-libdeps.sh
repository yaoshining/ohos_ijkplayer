#!/usr/bin/env bash
# Build the static mbedTLS / libdav1d / libxml2 closure for the FFmpeg 8
# OpenHarmony SDK. These are installed into the same isolated dependency
# sysroot as the Samba/GnuTLS closure produced by build-libsmbclient.sh, so
# FFmpeg can resolve every capability through one PKG_CONFIG_LIBDIR.
#
# 依赖（全部静态，供 FFmpeg --enable-* 静态链接进六个 shared libraries）：
#   mbedTLS 3.6.4  -> libmbedtls.a / libmbedx509.a / libmbedcrypto.a (+ .pc)
#   libdav1d 1.5.1 -> libdav1d.a (+ dav1d.pc)
#   libxml2 2.15.1 -> libxml2.a (+ libxml-2.0.pc, 静态链接 zlib)
#
# 关键技术点：
#   - OHOS sysroot 基于 musl，必须向编译/链接传递 __MUSL__=1 与 -fPIC。
#   - meson 交叉构建通过 --cross-file 传递 --target/--sysroot，宿主 pkg-config
#     经 PKG_CONFIG_LIBDIR 指向本 sysroot 的 .pc 目录以解析 zlib。
set -euo pipefail

log() { printf '\033[1;34m[deps]\033[0m %s\n' "$*"; }
die() { printf '\033[1;31m[deps] 错误：%s\033[0m\n' "$*" >&2; exit 1; }

# ---------------- 可配置入口 ----------------
: "${OHOS_NDK:?OHOS_NDK must point to an OpenHarmony NDK}"
: "${WORK_DIR:=$(pwd)/out/ffmpeg8-deps-work}"
: "${PREFIX:=$(pwd)/out/ffmpeg8-deps-sysroot/${OHOS_ARCH:-arm64-v8a}}"
: "${JOBS:=$(getconf _NPROCESSORS_ONLN 2>/dev/null || sysctl -n hw.ncpu 2>/dev/null || echo 4)}"

# 固定版本与 SHA-256，保证可复现构建。
V_MBEDTLS=3.6.4
MBEDTLS_SHA256=ec35b18a6c593cf98c3e30db8b98ff93e8940a8c4e690e66b41dfc011d678110
V_DAV1D=1.5.1
DAV1D_SHA256=4eddffd108f098e307b93c9da57b6125224dc5877b1b3d157b31be6ae8f1f093
V_LIBXML2=2.15.1
LIBXML2_SHA256=c008bac08fd5c7b4a87f7b8a71f283fa581d80d80ff8d2efd3b26224c39bc54c

MBEDTLS_URL="https://github.com/Mbed-TLS/mbedtls/releases/download/mbedtls-${V_MBEDTLS}/mbedtls-${V_MBEDTLS}.tar.bz2"
DAV1D_URL="https://code.videolan.org/videolan/dav1d/-/archive/${V_DAV1D}/dav1d-${V_DAV1D}.tar.bz2"
LIBXML2_URL="https://download.gnome.org/sources/libxml2/2.15/libxml2-${V_LIBXML2}.tar.xz"

OHOS_ARCH=${OHOS_ARCH:-arm64-v8a}
case "$OHOS_ARCH" in
  arm64-v8a) TARGET=aarch64-unknown-linux-ohos; CPU_FAMILY=aarch64; CMAKE_PROC=aarch64 ;;
  x86_64) TARGET=x86_64-unknown-linux-ohos; CPU_FAMILY=x86_64; CMAKE_PROC=x86_64 ;;
  *) die "unsupported OHOS_ARCH: $OHOS_ARCH (expected arm64-v8a or x86_64)" ;;
esac
SYSROOT=${OHOS_SYSROOT:-"$OHOS_NDK/sysroot"}
TOOLCHAIN=${OHOS_LLVM_BIN:-"$OHOS_NDK/llvm/bin"}
if [ ! -d "$SYSROOT" ] && [ -d "$OHOS_NDK/native/sysroot" ]; then SYSROOT="$OHOS_NDK/native/sysroot"; fi
if [ ! -d "$TOOLCHAIN" ] && [ -d "$OHOS_NDK/native/llvm/bin" ]; then TOOLCHAIN="$OHOS_NDK/native/llvm/bin"; fi

[ -d "$OHOS_NDK" ] || die "OHOS_NDK 不存在：$OHOS_NDK（请在预装 DevEco Studio 的 runner 上运行）"
[ -x "$TOOLCHAIN/clang" ] || die "missing LLVM clang: $TOOLCHAIN/clang"
[ -x "$TOOLCHAIN/llvm-ar" ] || die "missing llvm-ar: $TOOLCHAIN/llvm-ar"
for c in curl tar shasum cmake meson ninja pkg-config; do
  command -v "$c" >/dev/null 2>&1 || die "缺少 $c"
done

mkdir -p "$PREFIX/lib/pkgconfig" "$PREFIX/include" "$WORK_DIR/downloads"

fetch_extract() {
  local url=$1 sha256=$2 archive=$3 strip=$4 dest=$5
  local archive_path="$WORK_DIR/downloads/$archive"
  if [ ! -f "$archive_path" ]; then
    log "下载 $archive"
    curl --fail --location --retry 3 --output "$archive_path" "$url"
  fi
  printf '%s  %s\n' "$sha256" "$archive_path" | shasum -a 256 --check --status || \
    die "checksum mismatch for $archive"
  if [ ! -d "$dest" ]; then
    mkdir -p "$dest"
    tar -C "$dest" --strip-components="$strip" -xf "$archive_path"
  fi
}

# meson 交叉文件：宿主 clang + --target/--sysroot 承载交叉语义。
CROSS_FILE="$WORK_DIR/crossfile-$OHOS_ARCH.ini"
cat > "$CROSS_FILE" <<EOF
[host_machine]
system = 'linux'
cpu_family = '$CPU_FAMILY'
cpu = '$OHOS_ARCH'
endian = 'little'

[binaries]
c = '$TOOLCHAIN/clang'
ar = '$TOOLCHAIN/llvm-ar'
strip = '$TOOLCHAIN/llvm-strip'
pkg-config = 'pkg-config'

[built-in options]
c_args = ['--target=$TARGET', '--sysroot=$SYSROOT', '-fPIC', '-D__MUSL__=1']
c_link_args = ['--target=$TARGET', '-fuse-ld=lld']
buildtype = 'release'
default_library = 'static'
wrap_mode = 'nodownload'
EOF

# ---------------- mbedTLS（CMake，纯 C） ----------------
build_mbedtls() {
  local src="$WORK_DIR/mbedtls-${V_MBEDTLS}"
  fetch_extract "$MBEDTLS_URL" "$MBEDTLS_SHA256" "mbedtls-${V_MBEDTLS}.tar.bz2" 1 "$src"
  if [ ! -f "$PREFIX/lib/libmbedtls.a" ]; then
    log "构建 mbedtls ${V_MBEDTLS}"
    cmake -S "$src" -B "$WORK_DIR/mbedtls-build" \
      -DCMAKE_SYSTEM_NAME=Linux -DCMAKE_SYSTEM_PROCESSOR="$CMAKE_PROC" \
      -DCMAKE_C_COMPILER="$TOOLCHAIN/clang" \
      -DCMAKE_C_FLAGS="--target=$TARGET --sysroot=$SYSROOT -fPIC -D__MUSL__=1" \
      -DCMAKE_AR="$TOOLCHAIN/llvm-ar" -DCMAKE_RANLIB="$TOOLCHAIN/llvm-ranlib" \
      -DCMAKE_INSTALL_PREFIX="$PREFIX" -DCMAKE_BUILD_TYPE=Release \
      -DENABLE_TESTING=OFF -DENABLE_PROGRAMS=OFF -DUSE_SHARED_MBEDTLS_LIBRARY=OFF
    cmake --build "$WORK_DIR/mbedtls-build" -j"$JOBS"
    cmake --install "$WORK_DIR/mbedtls-build"
  else
    log "mbedtls 已构建，跳过"
  fi
}

# ---------------- libdav1d（meson） ----------------
build_dav1d() {
  local src="$WORK_DIR/dav1d-${V_DAV1D}"
  fetch_extract "$DAV1D_URL" "$DAV1D_SHA256" "dav1d-${V_DAV1D}.tar.bz2" 1 "$src"
  if [ ! -f "$PREFIX/lib/libdav1d.a" ]; then
    log "构建 dav1d ${V_DAV1D}"
    meson setup "$WORK_DIR/dav1d-build" "$src" \
      --cross-file "$CROSS_FILE" --prefix="$PREFIX" \
      -Denable_tests=false -Denable_tools=false
    meson compile -C "$WORK_DIR/dav1d-build" -j "$JOBS"
    meson install -C "$WORK_DIR/dav1d-build"
  else
    log "dav1d 已构建，跳过"
  fi
}

# ---------------- libxml2（meson，静态链接 zlib） ----------------
build_libxml2() {
  local src="$WORK_DIR/libxml2-${V_LIBXML2}"
  fetch_extract "$LIBXML2_URL" "$LIBXML2_SHA256" "libxml2-${V_LIBXML2}.tar.xz" 1 "$src"
  if [ ! -f "$PREFIX/lib/libxml2.a" ]; then
    log "构建 libxml2 ${V_LIBXML2}"
    # 让宿主 pkg-config 在交叉构建中解析 zlib.pc（位于同一 sysroot）。
    export PKG_CONFIG_LIBDIR="$PREFIX/lib/pkgconfig"
    meson setup "$WORK_DIR/libxml2-build" "$src" \
      --cross-file "$CROSS_FILE" --prefix="$PREFIX" \
      -Ddocs=disabled -Dzlib=enabled -Dsax1=enabled
    meson compile -C "$WORK_DIR/libxml2-build" -j "$JOBS"
    meson install -C "$WORK_DIR/libxml2-build"
  else
    log "libxml2 已构建，跳过"
  fi
}

build_mbedtls
build_dav1d
build_libxml2

[ -f "$PREFIX/lib/libmbedtls.a" ] || die "missing libmbedtls.a"
[ -f "$PREFIX/lib/libdav1d.a" ] || die "missing libdav1d.a"
[ -f "$PREFIX/lib/libxml2.a" ] || die "missing libxml2.a"
[ -f "$PREFIX/lib/pkgconfig/mbedtls.pc" ] || die "missing mbedtls.pc"
[ -f "$PREFIX/lib/pkgconfig/dav1d.pc" ] || die "missing dav1d.pc"
[ -f "$PREFIX/lib/pkgconfig/libxml-2.0.pc" ] || die "missing libxml-2.0.pc"
[ -f "$PREFIX/include/mbedtls/ssl.h" ] || die "missing mbedtls/ssl.h"
[ -f "$PREFIX/include/dav1d/dav1d.h" ] || die "missing dav1d/dav1d.h"
[ -f "$PREFIX/include/libxml2/libxml/xmlversion.h" ] || die "missing libxml2/libxml/xmlversion.h"

log "静态依赖闭包安装完成：$PREFIX"
