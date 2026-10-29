#!/bin/bash
set -euo pipefail
# 输入为锁定版本源码仓库与静态 SMB/GnuTLS sysroot；输出目录必须全新。
# 底层构建器；通过 producer-sdk.py 调用以生成摘要、许可和 SDK manifest。
root=$(cd "$(dirname "$0")" && pwd)
source "$root/build-env.sh"
: "${OHOS_NDK:?请指定 OpenHarmony native NDK}"
: "${FFMPEG_SOURCE_REPO:?请指定含 FFmpeg 8 锁定提交的源码仓库}"
: "${SMB_PREFIX:?请指定静态 SMB/GnuTLS sysroot}"
: "${OUTPUT_ROOT:?请指定新的构建输出目录}"
[ ! -e "$OUTPUT_ROOT" ] || { echo '拒绝覆盖已有输出目录' >&2; exit 1; }
mkdir -p "$OUTPUT_ROOT/source" "$OUTPUT_ROOT/build"
ffmpeg_commit=140fd653aed8cad774f991ba083e2d01e86420c7
builder_commit=1bab837e662ffa47ce51efd0720d3ed7c4988944
git -C "$FFMPEG_SOURCE_REPO" archive "$ffmpeg_commit" > "$OUTPUT_ROOT/source.tar"
tar -xf "$OUTPUT_ROOT/source.tar" -C "$OUTPUT_ROOT/source"
for name in support-av3a-audio-vivid.patch support-zero-copy-hardware-decode.patch; do
  cp "$root/patches/ohcodec/$name" "$OUTPUT_ROOT/$name"
  patch -d "$OUTPUT_ROOT/source" -p1 < "$OUTPUT_ROOT/$name"
done
patch -d "$OUTPUT_ROOT/source" -p1 < "$root/patches/0001-libsmbclient-private-credentials.patch"
prepare_build_inputs "$OUTPUT_ROOT/build" "$SMB_PREFIX" "$OHOS_NDK"
ndk=./toolchain
unset CFLAGS CXXFLAGS CPPFLAGS LDFLAGS CPATH LIBRARY_PATH C_INCLUDE_PATH CPLUS_INCLUDE_PATH SDKROOT MACOSX_DEPLOYMENT_TARGET
prepare_source_link "$OUTPUT_ROOT"
cd "$OUTPUT_ROOT/build"
"$OUTPUT_ROOT/source/configure" --prefix="$FFMPEG_CONFIGURE_PREFIX" --arch=aarch64 --target-os=linux --enable-cross-compile \
 --cc="$ndk/llvm/bin/aarch64-unknown-linux-ohos-clang" --cxx="$ndk/llvm/bin/aarch64-unknown-linux-ohos-clang++" \
 --ar="$ndk/llvm/bin/llvm-ar" --nm="$ndk/llvm/bin/llvm-nm" --ranlib="$ndk/llvm/bin/llvm-ranlib" --strip="$ndk/llvm/bin/llvm-strip" \
 --sysroot="$ndk/sysroot" --extra-cflags="$FFMPEG_INPUT_CFLAGS" --extra-ldflags="$FFMPEG_INPUT_LDFLAGS" \
 --pkg-config-flags=--static --disable-static --enable-shared --enable-pic --disable-programs --disable-doc --disable-avdevice \
 --disable-autodetect --disable-xlib --disable-sdl2 --enable-network --enable-gnutls --enable-libsmbclient --enable-gpl --enable-version3 --disable-nonfree --enable-ohcodec
make -j"${JOBS:-8}"
make install DESTDIR="$OUTPUT_ROOT/install"
mv "$OUTPUT_ROOT/install$FFMPEG_CONFIGURE_PREFIX" "$OUTPUT_ROOT/prefix"
verify_build_inputs "$OUTPUT_ROOT/build"

printf '%s\n' "ffmpeg_commit=$ffmpeg_commit" "builder_commit=$builder_commit" > "$OUTPUT_ROOT/SOURCE.txt"
python3 - "$OUTPUT_ROOT/prefix/lib" <<'PYMETA'
from pathlib import Path
import hashlib, sys
root=Path(sys.argv[1])
rows=[]
for name in ['libavcodec.so.62','libavformat.so.62','libavutil.so.60','libavfilter.so.11','libswresample.so.6','libswscale.so.9']:
    rows.append(hashlib.sha256((root/name).read_bytes()).hexdigest()+'  '+name)
(root.parent/'SHA256SUMS').write_text('\n'.join(rows)+'\n')
PYMETA
