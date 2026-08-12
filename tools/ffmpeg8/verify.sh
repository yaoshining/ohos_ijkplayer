#!/usr/bin/env bash
# Validate the packaged OpenHarmony ELF ABI and record linker metadata.
set -euo pipefail

SCRIPT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
PREFIX=${1:-}
[ -n "$PREFIX" ] || { echo "usage: $0 <ffmpeg-sdk-prefix>" >&2; exit 2; }
[ -d "$PREFIX/lib" ] || { echo "error: missing SDK lib directory: $PREFIX/lib" >&2; exit 1; }

find_readelf() {
    if [ -n "${LLVM_READELF:-}" ]; then
        printf '%s\n' "$LLVM_READELF"
        return
    fi
    if [ -n "${OHOS_NDK:-}" ]; then
        local candidate="${OHOS_LLVM_BIN:-$OHOS_NDK/llvm/bin}/llvm-readelf"
        [ -x "$candidate" ] && { printf '%s\n' "$candidate"; return; }
        candidate=$(find "$OHOS_NDK" -type f -name llvm-readelf -perm -111 -print -quit)
        [ -n "$candidate" ] && { printf '%s\n' "$candidate"; return; }
    fi
    command -v llvm-readelf 2>/dev/null || true
}

READELF=$(find_readelf)
[ -n "$READELF" ] && [ -x "$READELF" ] || { echo "error: llvm-readelf not found; set OHOS_NDK or LLVM_READELF" >&2; exit 1; }

REPORT="$PREFIX/ELF-REPORT.txt"
TARGET=unknown
ARCHITECTURE=unknown
if [ -f "$PREFIX/VERSION" ]; then
    TARGET=$(awk -F= '$1 == "target" { print $2; exit }' "$PREFIX/VERSION")
    ARCHITECTURE=$(awk -F= '$1 == "architecture" { print $2; exit }' "$PREFIX/VERSION")
fi
case "$TARGET:$ARCHITECTURE" in
    aarch64-unknown-linux-ohos*:arm64-v8a) ;;
    x86_64-unknown-linux-ohos*:x86_64) ;;
    *) echo "error: unsupported OpenHarmony SDK target: $TARGET ($ARCHITECTURE)" >&2; exit 1 ;;
esac
{
    echo "FFmpeg OpenHarmony ELF verification"
    echo "target=$TARGET"
    echo "architecture=$ARCHITECTURE"
    echo "readelf=$READELF"
    echo
} > "$REPORT"

for library in avcodec avformat avutil avfilter swscale swresample; do
    path="$PREFIX/lib/lib${library}.so"
    [ -e "$path" ] || { echo "error: missing $path" >&2; exit 1; }
    header=$("$READELF" --file-header "$path")
    dynamic=$("$READELF" --dynamic "$path")
    class=$(printf '%s\n' "$header" | awk -F: '/Class:/ { gsub(/^ +/, "", $2); print $2; exit }')
    machine=$(printf '%s\n' "$header" | awk -F: '/Machine:/ { gsub(/^ +/, "", $2); print $2; exit }')
    osabi=$(printf '%s\n' "$header" | awk -F: '/OS\/ABI:/ { gsub(/^ +/, "", $2); print $2; exit }')
    [ "$class" = "ELF64" ] || { echo "error: $path is not ELF64 ($class)" >&2; exit 1; }
    case "$ARCHITECTURE" in
        arm64-v8a) case "$machine" in *AArch64*) ;; *) echo "error: $path is not AArch64 ($machine)" >&2; exit 1;; esac ;;
        x86_64) case "$machine" in *X86-64*) ;; *) echo "error: $path is not x86_64 ($machine)" >&2; exit 1;; esac ;;
    esac
    soname=$(printf '%s\n' "$dynamic" | awk -F'[][]' '/SONAME/ { print $2; exit }')
    [ -n "$soname" ] || { echo "error: $path has no SONAME" >&2; exit 1; }
    {
        echo "library=lib${library}.so"
        echo "size_bytes=$(wc -c < "$path" | tr -d ' ')"
        echo "class=$class"
        echo "machine=$machine"
        echo "os_abi=$osabi"
        echo "soname=$soname"
        echo "dt_needed:"
        printf '%s\n' "$dynamic" | awk -F'[][]' '/NEEDED/ { print "  " $2 }'
        echo
    } >> "$REPORT"
done

echo "ELF verification passed; report: $REPORT"
