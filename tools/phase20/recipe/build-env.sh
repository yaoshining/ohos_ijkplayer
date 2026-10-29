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

# 每条构建链各自绑定实际输入；configure/编译命令只使用本地稳定相对入口。
build_input_bindings() {
  python3 - "$@" <<'PYINPUTS'
from pathlib import Path
import json, os, sys
mode=sys.argv[1];build=Path(sys.argv[2]).resolve();record=build/'input-bindings.json'
if mode=='create':
    deps=Path(sys.argv[3]).resolve();ndk=Path(sys.argv[4]).resolve()
    for p in [build,deps/'include',deps/'lib/pkgconfig',ndk/'sysroot',ndk/'llvm/bin']:
        if not p.is_dir():raise ValueError('构建输入目录缺失: '+str(p))
    if not os.access(ndk/'llvm/bin/aarch64-unknown-linux-ohos-clang',os.X_OK):raise ValueError('目标编译器缺失或不可执行')
    if record.exists() or any(os.path.lexists(build/n) for n in ['deps','toolchain']):raise ValueError('拒绝覆盖已有构建输入绑定')
    rows=[]
    for role,path in [('deps',deps),('toolchain',ndk)]:
        (build/role).symlink_to(path,target_is_directory=True)
        rows.append({'role':role,'logicalPath':'./'+role,'resolvedPath':str(path),'linkTarget':str(path)})
    record.write_text(json.dumps({'schemaVersion':1,'inputs':rows},indent=2)+'\n')
elif mode=='verify':
    data=json.loads(record.read_text())
    if data.get('schemaVersion')!=1 or {x['role'] for x in data['inputs']}!={'deps','toolchain'}:raise ValueError('构建输入绑定无效')
    for row in data['inputs']:
        p=build/row['role']
        if not p.is_symlink() or not p.is_dir() or str(p.resolve())!=row['resolvedPath'] or os.readlink(p)!=row['linkTarget']:raise ValueError('构建输入绑定发生变化: '+str(p))
else:raise ValueError('未知构建输入绑定操作')
PYINPUTS
}
prepare_build_inputs() {
  build_input_bindings create "$@" || return
  export FFMPEG_INPUT_CFLAGS='-fPIC -I./deps/include'
  export FFMPEG_INPUT_LDFLAGS='-L./deps/lib'
  export PKG_CONFIG_PATH='./deps/lib/pkgconfig'
  export PKG_CONFIG_LIBDIR="$PKG_CONFIG_PATH"
  export PKG_CONFIG_SYSROOT_DIR=
}
verify_build_inputs() {
  build_input_bindings verify "$1"
}
