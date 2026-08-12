#!/usr/bin/env bash
# Static contract checks are intentionally runnable without an OpenHarmony NDK.
set -euo pipefail
root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
build="$root/build.sh"; smb="$root/build-libsmbclient.sh"; verify="$root/verify.sh"
grep -Fq -- '--disable-static' "$build"
grep -Fq -- '--enable-shared' "$build"
grep -Fq -- '--enable-pic' "$build"
grep -Fq -- '--enable-cross-compile' "$build"
grep -Fq -- '--enable-libsmbclient' "$build"
grep -Fq -- '--enable-gpl' "$build"
grep -Fq -- '--pkg-config-flags=--static' "$build"
grep -Fq 'PKG_CONFIG_LIBDIR="$SMB_SYSROOT/lib/pkgconfig"' "$build"
grep -Fq 'libsmbclient_linkage=static-closure' "$build"
grep -Fq 'libav*.a' "$verify"
grep -Fq 'libsmbclient\.so' "$verify"
grep -Fq 'ELF64' "$verify"
grep -Fq 'libsmbclient' "$verify"
grep -Fq 'SAMBA_ARCHIVE_SHA256' "$smb"
grep -Fq 'https://www.mirrorservice.org/sites/ftp.gnupg.org/gcrypt/gnutls/v3.8/gnutls-3.8.7.tar.xz' "$smb"
! grep -Fq 'https://www.gnupg.org/ftp/gcrypt/gnutls/v3.8/gnutls-3.8.7.tar.xz' "$smb"
grep -Fq 'Libs.private:' "$smb"
! grep -Fq 'git reset --hard' "$smb"
echo 'FFmpeg 8 SMB SDK contract test passed'
