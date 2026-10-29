#!/bin/bash
# 研究阶段未执行。使用已核对的输入包；不允许指向旧 target/cache 作为输出。
set -euo pipefail
bundle=${1:?固定输入包绝对目录}
run=${2:?全新运行目录}
sdk=${3:?固定OHOS native SDK目录}
case "$bundle:$run:$sdk" in /*:/*:/*) ;; *) echo '所有参数须为绝对路径' >&2; exit 2;; esac
[[ ! -e "$run" && ! -L "$run" ]] || { echo 'run root 必须不存在' >&2; exit 2; }
[[ -d "$bundle/source/dolby_vision" && -d "$bundle/vendor" && -x "$bundle/toolchain/bin/rustc" && -x "$bundle/tools/cargo-cinstall" ]]
ancestor=$(dirname "$run")
while [[ "$ancestor" != / ]]; do
  [[ ! -f "$ancestor/.cargo/config" && ! -f "$ancestor/.cargo/config.toml" ]] || { echo "拒绝祖先Cargo配置: $ancestor" >&2; exit 2; }
  ancestor=$(dirname "$ancestor")
done
mkdir -p "$run"/{source,cargo-home,rustup-empty,logs,tmp,host-cache,home}
cp -R "$bundle/source/." "$run/source/"
# source 来自固定 git archive，不能带 target 或祖先 .cargo 配置；包构建阶段做 exact 文件集合门禁。
[[ ! -e "$run/source/dolby_vision/target" && ! -e "$run/source/.cargo" && ! -e "$run/source/dolby_vision/.cargo" ]]
# 本配置仅产生于新的 CARGO_HOME，不修改源码或原 ~/.cargo、~/.rustup。
cat > "$run/cargo-home/config.toml" <<EOF
[net]
offline = true
[source.crates-io]
replace-with = "fixed-vendor"
[source.fixed-vendor]
directory = "$bundle/vendor"
EOF
# 整个 toolchain 根含其动态库、host std 与 OHOS std；使用 direct binaries，绕开 rustup proxy 和自动下载。
base=(env -i PATH="$bundle/tools:$bundle/toolchain/bin:/usr/bin:/bin" LANG=C LC_ALL=C
  HOME="$run/home" CARGO_BUILD_JOBS=8 CARGO_HOME="$run/cargo-home" RUSTUP_HOME="$run/rustup-empty"
  CARGO="$bundle/toolchain/bin/cargo" RUSTC="$bundle/toolchain/bin/rustc" RUSTDOC="$bundle/toolchain/bin/rustdoc"
  CARGO_NET_OFFLINE=true CARGO_INCREMENTAL=0 TMPDIR="$run/tmp" XDG_CACHE_HOME="$run/host-cache"
  PYTHONDONTWRITEBYTECODE=1)
cd "$run/source/dolby_vision"
# 默认 release + capi，与原 cinstall 目标一致；未把 release-deploy 的 thin LTO/strip 误套到 release。
# Rust 路径映射是隔离目录重现性的新显式参数，需在后续 fresh 对照中验证，不能宣称等于旧缓存字节。
"${base[@]}" CARGO_TARGET_DIR="$run/target-ohos" \
  CARGO_TARGET_AARCH64_UNKNOWN_LINUX_OHOS_LINKER="$sdk/llvm/bin/clang" \
  CARGO_TARGET_AARCH64_UNKNOWN_LINUX_OHOS_RUSTFLAGS="--remap-path-prefix=$run=. -Clink-arg=--target=aarch64-linux-ohos -Clink-arg=--sysroot=$sdk/sysroot" \
  AR_aarch64_unknown_linux_ohos="$sdk/llvm/bin/llvm-ar" \
  CC_aarch64_unknown_linux_ohos="$sdk/llvm/bin/clang" \
  CFLAGS_aarch64_unknown_linux_ohos="--target=aarch64-linux-ohos --sysroot=$sdk/sysroot" \
  "$bundle/toolchain/bin/cargo" cinstall --frozen --release --target=aarch64-unknown-linux-ohos \
  --library-type=staticlib --prefix=/usr/local --destdir="$run/install" --libdir=lib -vv \
  > "$run/logs/cinstall.log" 2>&1
# 单独 host target；只执行宿主 Rust 单元测试，不执行 OHOS 产物。
"${base[@]}" CARGO_TARGET_DIR="$run/target-host-tests" \
  "$bundle/toolchain/bin/cargo" test --frozen --lib --features capi -vv \
  > "$run/logs/host-tests.log" 2>&1
# 可选扩展语义测试（同一84crate vendor已锁 xml/serde/dev deps；需保留整个 source/assets）。
"${base[@]}" CARGO_TARGET_DIR="$run/target-host-tests" \
  "$bundle/toolchain/bin/cargo" test --frozen --lib --features capi,xml,serde -vv \
  > "$run/logs/host-tests-xml-serde.log" 2>&1
# 后续必须：锁文件/source/vendor/toolchain 前后 pin；实际 rustc 命令与 .d、std输入、header/pc/451成员等门禁；另一路绝对长度不同 fresh root 比较。
