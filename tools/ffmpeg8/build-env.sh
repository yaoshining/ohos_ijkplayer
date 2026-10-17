#!/usr/bin/env bash
# 固定归档源码的版本，避免 FFmpeg version.sh 发现父仓 Git。
export revision=8.0
export SOURCE_DATE_EPOCH=1755820644
export LC_ALL=C
export TZ=UTC
export FFMPEG_CONFIGURE_PREFIX=${FFMPEG_CONFIGURE_PREFIX:-/opt/ohos-ffmpeg8}
case "$FFMPEG_CONFIGURE_PREFIX" in
  /*) ;;
  *) echo 'configure prefix 必须是绝对路径' >&2; return 2 2>/dev/null || exit 2 ;;
esac
case "$FFMPEG_CONFIGURE_PREFIX/" in
  *'/../'*|*'/./'*|//|/) echo '拒绝不安全的 configure prefix' >&2; return 2 2>/dev/null || exit 2 ;;
esac
# Makefile 使用 revision=$(REVISION)，必须同时固定大写 make 变量。
export REVISION=8.0
prepare_source_link() {
  local output=$1
  [ ! -e "$output/build/src" ] && [ ! -L "$output/build/src" ] || return 2
  ln -s ../source "$output/build/src"
}
