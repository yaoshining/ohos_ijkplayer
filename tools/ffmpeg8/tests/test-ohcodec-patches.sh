#!/usr/bin/env bash
# 在锁定 git 源码的独立临时目录验证三份补丁；不会修改输入仓库。
set -euo pipefail
root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
repo=${1:?usage: test-ohcodec-patches.sh <ffmpeg-git-repo>}
work=$(mktemp -d)
trap 'rm -rf "$work"' EXIT
git -C "$repo" archive 140fd653aed8cad774f991ba083e2d01e86420c7 > "$work/source.tar"
mkdir "$work/source"
tar -xf "$work/source.tar" -C "$work/source"
for file in "$root/patches/ohcodec/support-av3a-audio-vivid.patch" "$root/patches/ohcodec/support-zero-copy-hardware-decode.patch" "$root/patches/0001-libsmbclient-private-credentials.patch"; do
    patch -d "$work/source" -p1 < "$file"
    patch -d "$work/source" -p1 -R --dry-run < "$file" >/dev/null
done
grep -Fq 'char *username;' "$work/source/libavformat/libsmbclient.c"
grep -Fq 'char *password;' "$work/source/libavformat/libsmbclient.c"
grep -Fq 'smbc_setOptionUserData(libsmbc->ctx, libsmbc);' "$work/source/libavformat/libsmbclient.c"
! grep -Eq 'av_(log|append_path_component).*password|smb://.*username|smb://.*password' "$work/source/libavformat/libsmbclient.c"
grep -Fq 'av_ohcodec_release_buffer' "$work/source/libavcodec/ohdec.c"
echo '锁定源码的 AV3A、OHCodec zero-copy、SMB 凭据补丁回归通过'
