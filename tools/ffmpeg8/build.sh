#!/usr/bin/env bash
# Build a reusable FFmpeg 8 shared-library SDK for OpenHarmony.
set -euo pipefail

SCRIPT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
REPO_ROOT=$(cd -- "$SCRIPT_DIR/../.." && pwd)

FFMPEG_VERSION=8.0
FFMPEG_ARCHIVE="ffmpeg-${FFMPEG_VERSION}.tar.xz"
FFMPEG_URL="https://ffmpeg.org/releases/${FFMPEG_ARCHIVE}"
FFMPEG_SHA256="b2751fccb6cc4c77708113cd78b561059b6fa904b24162fa0be2d60273d27b8e"
OHOS_ARCH=${OHOS_ARCH:-arm64-v8a}
case "$OHOS_ARCH" in
    arm64-v8a)
        TARGET_TRIPLE=aarch64-unknown-linux-ohos
        ARCH=aarch64
        ELF_MACHINE=AArch64
        ;;
    x86_64)
        TARGET_TRIPLE=x86_64-unknown-linux-ohos
        ARCH=x86_64
        ELF_MACHINE='Advanced Micro Devices X86-64'
        ;;
    *)
        echo "error: unsupported OHOS_ARCH: $OHOS_ARCH (supported: arm64-v8a, x86_64)" >&2
        exit 2
        ;;
esac
JOBS=${JOBS:-$(getconf _NPROCESSORS_ONLN 2>/dev/null || sysctl -n hw.ncpu 2>/dev/null || echo 4)}
WORK_DIR=${FFMPEG8_WORK_DIR:-"$REPO_ROOT/out/ffmpeg8-work"}
PREFIX_IS_CUSTOM=0
if [ "${FFMPEG8_PREFIX+x}" = x ]; then
    PREFIX=$FFMPEG8_PREFIX
    PREFIX_IS_CUSTOM=1
else
    PREFIX="$REPO_ROOT/out/ffmpeg8/$OHOS_ARCH"
fi

case "$JOBS" in
    ''|*[!0-9]*|0) echo "error: JOBS must be a positive integer: $JOBS" >&2; exit 2 ;;
esac

fail() {
    echo "error: $*" >&2
    exit 1
}

[ -n "$PREFIX" ] || fail "FFMPEG8_PREFIX must not be empty"

require_command() {
    command -v "$1" >/dev/null 2>&1 || fail "required command not found: $1"
}

[ -n "${OHOS_NDK:-}" ] || fail "OHOS_NDK must point to an OpenHarmony NDK installation"
[ -d "$OHOS_NDK" ] || fail "OHOS_NDK is not a directory: $OHOS_NDK"
require_command curl
require_command tar
require_command shasum
require_command make

LLVM_BIN=${OHOS_LLVM_BIN:-"$OHOS_NDK/llvm/bin"}
[ -d "$LLVM_BIN" ] || LLVM_BIN=$(find "$OHOS_NDK" -type d -path '*/llvm/bin' -print -quit)
[ -n "$LLVM_BIN" ] && [ -d "$LLVM_BIN" ] || fail "cannot find llvm/bin below OHOS_NDK; set OHOS_LLVM_BIN explicitly"

CC=${CC:-"$LLVM_BIN/${TARGET_TRIPLE}-clang"}
CXX=${CXX:-"$LLVM_BIN/${TARGET_TRIPLE}-clang++"}
AR=${AR:-"$LLVM_BIN/llvm-ar"}
NM=${NM:-"$LLVM_BIN/llvm-nm"}
RANLIB=${RANLIB:-"$LLVM_BIN/llvm-ranlib"}
STRIP=${STRIP:-"$LLVM_BIN/llvm-strip"}
for tool in "$CC" "$CXX" "$AR" "$NM" "$RANLIB" "$STRIP"; do
    [ -x "$tool" ] || fail "required OpenHarmony LLVM tool is unavailable: $tool"
done

SYSROOT=${OHOS_SYSROOT:-"$OHOS_NDK/sysroot"}
[ -d "$SYSROOT" ] || fail "cannot find NDK sysroot: $SYSROOT; set OHOS_SYSROOT explicitly"

DOWNLOAD_DIR="$WORK_DIR/downloads"
SOURCE_DIR="$WORK_DIR/ffmpeg-${FFMPEG_VERSION}"
BUILD_DIR="$WORK_DIR/build-$OHOS_ARCH"
ARCHIVE_PATH="$DOWNLOAD_DIR/$FFMPEG_ARCHIVE"

mkdir -p "$DOWNLOAD_DIR" "$WORK_DIR"
if [ ! -f "$ARCHIVE_PATH" ]; then
    curl --fail --location --retry 3 --output "$ARCHIVE_PATH" "$FFMPEG_URL"
fi
actual_sha=$(shasum -a 256 "$ARCHIVE_PATH" | awk '{print $1}')
[ "$actual_sha" = "$FFMPEG_SHA256" ] || fail "checksum mismatch for $ARCHIVE_PATH: expected $FFMPEG_SHA256, got $actual_sha"

rm -rf "$SOURCE_DIR" "$BUILD_DIR"
PREFIX_MARKER="$PREFIX/.ffmpeg8-ohos-sdk-managed"
if [ -e "$PREFIX" ] || [ -L "$PREFIX" ]; then
    if [ "$PREFIX_IS_CUSTOM" -eq 1 ]; then
        [ -d "$PREFIX" ] &&
            [ -f "$PREFIX_MARKER" ] &&
            [ "$(cat "$PREFIX_MARKER")" = "ffmpeg8-ohos-sdk-v1" ] ||
            fail "refusing to remove unmanaged FFMPEG8_PREFIX: $PREFIX; clean it explicitly or use a new path"
    fi
    rm -rf -- "$PREFIX"
fi
mkdir -p "$PREFIX"
printf '%s\n' "ffmpeg8-ohos-sdk-v1" > "$PREFIX_MARKER"

tar -C "$WORK_DIR" -xf "$ARCHIVE_PATH"
[ -d "$SOURCE_DIR" ] || fail "archive did not create expected source directory: $SOURCE_DIR"
mkdir -p "$BUILD_DIR"
cp -a "$SOURCE_DIR/." "$BUILD_DIR/"

# Keep FFmpeg's stock component boundaries and broad built-in media support.
# External GPL/nonfree codecs are deliberately excluded for a reusable LGPL SDK.
CONFIGURE_OPTIONS=(
    --prefix="$PREFIX"
    --arch="$ARCH"
    --target-os=linux
    --enable-cross-compile
    --cc="$CC"
    --cxx="$CXX"
    --ar="$AR"
    --nm="$NM"
    --ranlib="$RANLIB"
    --strip="$STRIP"
    --sysroot="$SYSROOT"
    --extra-cflags="--target=${TARGET_TRIPLE} -fPIC"
    --extra-ldflags="--target=${TARGET_TRIPLE}"
    --disable-static
    --enable-shared
    --enable-pic
    --disable-programs
    --disable-doc
    --disable-avdevice
    --disable-autodetect
    --disable-xlib
    --disable-sdl2
    --enable-network
    --enable-protocol=file,http,tcp,httpproxy,rtmp,rtp,udp,crypto,data,pipe,concat,subfile,cache,async
    --disable-gpl
    --disable-nonfree
)

pushd "$BUILD_DIR" >/dev/null
./configure "${CONFIGURE_OPTIONS[@]}"
make -j"$JOBS"
make install
popd >/dev/null

# These versions are the ABI contract required by VidAll_TV headers.
version_from_header() {
    local header=$1 macro=$2
    awk -v macro="$macro" '$1 == "#define" && $2 == macro { print $3; exit }' "$header"
}
assert_version() {
    local include_dir=$1 library=$2 prefix=$3 expected=$4
    local major minor micro actual
    local major_header="$include_dir/lib${library}/version_major.h"
    [ -f "$major_header" ] || major_header="$include_dir/lib${library}/version.h"
    major=$(version_from_header "$major_header" "${prefix}_VERSION_MAJOR")
    minor=$(version_from_header "$include_dir/lib${library}/version.h" "${prefix}_VERSION_MINOR")
    micro=$(version_from_header "$include_dir/lib${library}/version.h" "${prefix}_VERSION_MICRO")
    actual="${major}.${minor}.${micro}"
    [ "$actual" = "$expected" ] || fail "unexpected $prefix version: expected $expected, got $actual"
}
assert_version "$PREFIX/include" avutil LIBAVUTIL 60.8.100
assert_version "$PREFIX/include" avcodec LIBAVCODEC 62.11.100
assert_version "$PREFIX/include" avformat LIBAVFORMAT 62.3.100

for library in avcodec avformat avutil avfilter swscale swresample; do
    [ -e "$PREFIX/lib/lib${library}.so" ] || fail "missing shared library: lib${library}.so"
done
[ ! -e "$PREFIX/lib/libffmpeg.so" ] || fail "unexpected monolithic libffmpeg.so was produced"

mkdir -p "$PREFIX/licenses"
cp "$BUILD_DIR/COPYING.LGPLv2.1" "$PREFIX/licenses/FFmpeg-LGPL-2.1-or-later.txt"
cat > "$PREFIX/VERSION" <<METADATA
ffmpeg_version=${FFMPEG_VERSION}
source_url=${FFMPEG_URL}
source_sha256=${FFMPEG_SHA256}
target=${TARGET_TRIPLE}
architecture=${OHOS_ARCH}
elf_machine=${ELF_MACHINE}
configuration=${CONFIGURE_OPTIONS[*]}
METADATA

generate_manifest() {
    local manifest="$PREFIX/MANIFEST.tsv"
    local temporary="$PREFIX/.MANIFEST.tsv.tmp.$$"
    if ! {
        printf 'path\tsize_bytes\n'
        find "$PREFIX" -type f \
            ! -path "$manifest" \
            ! -path "$PREFIX/.MANIFEST.tsv.tmp.*" \
            -print0 |
            LC_ALL=C sort -z |
            while IFS= read -r -d '' file; do
                printf '%s\t%s\n' "${file#"$PREFIX/"}" "$(wc -c < "$file" | tr -d ' ')"
            done
    } > "$temporary"; then
        rm -f -- "$temporary"
        return 1
    fi
    if ! mv -f -- "$temporary" "$manifest"; then
        rm -f -- "$temporary"
        return 1
    fi
}

"$SCRIPT_DIR/verify.sh" "$PREFIX"

# Emit the final inventory only after ELF verification has added its report.
generate_manifest

echo "FFmpeg ${FFMPEG_VERSION} OpenHarmony SDK installed at: $PREFIX"
