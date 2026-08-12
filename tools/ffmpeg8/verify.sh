#!/usr/bin/env bash
# Validate packaged OpenHarmony FFmpeg 8 GPL SMB SDK and record ELF metadata.
set -euo pipefail
PREFIX=${1:-}
[ -n "$PREFIX" ] || { echo "usage: $0 <ffmpeg-sdk-prefix>" >&2; exit 2; }
[ -d "$PREFIX/lib" ] || { echo "error: missing SDK lib directory: $PREFIX/lib" >&2; exit 1; }
fail() { echo "error: $*" >&2; exit 1; }
expected_soname() { case "$1" in avcodec) echo libavcodec.so.62;; avformat) echo libavformat.so.62;; avutil) echo libavutil.so.60;; avfilter) echo libavfilter.so.11;; swscale) echo libswscale.so.9;; swresample) echo libswresample.so.6;; *) return 1;; esac; }
find_tool() {
    local env_name=$1 executable=$2 candidate
    candidate=${!env_name:-}
    [ -n "$candidate" ] && [ -x "$candidate" ] && { echo "$candidate"; return; }
    if [ -n "${OHOS_NDK:-}" ]; then
        candidate="${OHOS_LLVM_BIN:-$OHOS_NDK/llvm/bin}/$executable"
        [ -x "$candidate" ] && { echo "$candidate"; return; }
        candidate=$(find "$OHOS_NDK" -type f -name "$executable" -perm -111 -print -quit)
        [ -n "$candidate" ] && { echo "$candidate"; return; }
    fi
    command -v "$executable" 2>/dev/null || true
}
READELF=$(find_tool LLVM_READELF llvm-readelf); NM=$(find_tool LLVM_NM llvm-nm)
[ -n "$READELF" ] && [ -x "$READELF" ] || fail "llvm-readelf not found; set OHOS_NDK or LLVM_READELF"
[ -n "$NM" ] && [ -x "$NM" ] || fail "llvm-nm not found; set OHOS_NDK or LLVM_NM"
TARGET=$(awk -F= '$1 == "target" {print $2; exit}' "$PREFIX/VERSION")
ARCHITECTURE=$(awk -F= '$1 == "architecture" {print $2; exit}' "$PREFIX/VERSION")
[ "$(awk -F= '$1 == "libsmbclient" {print $2; exit}' "$PREFIX/VERSION")" = enabled ] || fail "VERSION does not record libsmbclient=enabled"
grep -Fxq -- '--enable-libsmbclient' "$PREFIX/configure-options.txt" || fail "missing --enable-libsmbclient configure proof"
grep -Fxq -- '--enable-gnutls' "$PREFIX/configure-options.txt" || fail "missing --enable-gnutls configure proof"
grep -Fxq -- '--enable-gpl' "$PREFIX/configure-options.txt" || fail "missing --enable-gpl configure proof"
[ "$(awk -F= '$1 == "https" {print $2; exit}' "$PREFIX/VERSION")" = enabled ] || fail "VERSION does not record https=enabled"
[ "$(awk -F= '$1 == "tls" {print $2; exit}' "$PREFIX/VERSION")" = enabled ] || fail "VERSION does not record tls=enabled"
for protocol in https tls; do grep -Fxq "$protocol" "$PREFIX/protocols.txt" || fail "protocol manifest does not contain $protocol"; done
case "$TARGET:$ARCHITECTURE" in aarch64-unknown-linux-ohos:arm64-v8a) expected_machine=AArch64;; x86_64-unknown-linux-ohos:x86_64) expected_machine=X86-64;; *) fail "unsupported target metadata: $TARGET ($ARCHITECTURE)";; esac
for item in include/libavcodec include/libavformat include/libavutil include/libavfilter include/libswresample include/libswscale lib/pkgconfig/libavcodec.pc lib/pkgconfig/libavformat.pc lib/pkgconfig/libavutil.pc lib/pkgconfig/libavfilter.pc lib/pkgconfig/libswresample.pc lib/pkgconfig/libswscale.pc licenses/FFmpeg-LGPL-2.1-or-later.txt licenses/GPL-3.0-or-later.txt VERSION configure-options.txt protocols.txt; do [ -e "$PREFIX/$item" ] || fail "missing exported SDK item: $item"; done
for pc in "$PREFIX"/lib/pkgconfig/*.pc; do ! grep -Fq "$PREFIX" "$pc" || fail "absolute build prefix leaked into $pc"; done
if find "$PREFIX" -type f -name 'libav*.a' -o -name 'libsw*.a' | grep -q .; then fail "static libav/libsw archive exported"; fi
REPORT="$PREFIX/ELF-REPORT.txt"
{ echo 'FFmpeg OpenHarmony ELF verification'; echo "target=$TARGET"; echo "architecture=$ARCHITECTURE"; echo "readelf=$READELF"; echo "nm=$NM"; echo 'libsmbclient=static-closure'; echo; } > "$REPORT"
for library in avcodec avformat avutil avfilter swscale swresample; do
    path="$PREFIX/lib/lib${library}.so"; [ -e "$path" ] || fail "missing $path"
    header=$("$READELF" --file-header "$path"); dynamic=$("$READELF" --dynamic "$path")
    class=$(printf '%s\n' "$header" | awk -F: '/Class:/ {gsub(/^ +/, "", $2); print $2; exit}')
    machine=$(printf '%s\n' "$header" | awk -F: '/Machine:/ {gsub(/^ +/, "", $2); print $2; exit}')
    [ "$class" = ELF64 ] || fail "$path is not ELF64 ($class)"; [[ "$machine" == *"$expected_machine"* ]] || fail "$path has wrong machine: $machine"
    soname=$(printf '%s\n' "$dynamic" | awk -F'[][]' '/SONAME/ {print $2; exit}'); [ "$soname" = "$(expected_soname "$library")" ] || fail "$path has unexpected SONAME: $soname"
    needed=$(printf '%s\n' "$dynamic" | awk -F'[][]' '/NEEDED/ {print $2}')
    ! printf '%s\n' "$dynamic" | grep -Eq '\((RPATH|RUNPATH)\)' || fail "$path contains an unexpected RPATH/RUNPATH"
    ! printf '%s\n' "$needed" | grep -Eq 'libsmbclient\.so|lib(gnutls|tasn1|nettle|hogweed|gmp|popt|z)\.so|libav[^ ]*\.a|libsw[^ ]*\.a' || fail "$path has forbidden dynamic/static dependency"
    { echo "library=lib${library}.so"; echo "size_bytes=$(wc -c < "$path" | tr -d ' ')"; echo "class=$class"; echo "machine=$machine"; echo "soname=$soname"; echo 'dt_needed:'; printf '%s\n' "$needed" | awk 'NF {print "  " $0}'; echo; } >> "$REPORT"
done
"$NM" -D "$PREFIX/lib/libavformat.so" | grep -Eq 'ff_libsmbclient_protocol|libsmbclient' || strings "$PREFIX/lib/libavformat.so" | grep -Fq 'libsmbclient' || fail 'libavformat does not expose the libsmbclient protocol'
for protocol in https tls; do
    strings "$PREFIX/lib/libavformat.so" | grep -Fxq "$protocol" || fail "libavformat does not contain the $protocol protocol"
done
echo "ELF verification passed; report: $REPORT"
