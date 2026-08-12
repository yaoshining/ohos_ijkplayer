#!/usr/bin/env bash
# Test that the FFmpeg 8 patch remains repeatable and keeps secrets out of URLs.
set -euo pipefail
script_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
archive=${1:?usage: $0 <ffmpeg-8.0.tar.xz>}
patch_file="$script_dir/patches/0001-libsmbclient-private-credentials.patch"
work=$(mktemp -d)
trap 'rm -rf "$work"' EXIT
tar -C "$work" -xf "$archive"
source="$work/ffmpeg-8.0/libavformat/libsmbclient.c"
patch -d "$work/ffmpeg-8.0" -p1 < "$patch_file"
patch -d "$work/ffmpeg-8.0" -R --dry-run -p1 < "$patch_file" >/dev/null
grep -Fq 'char *username;' "$source"
grep -Fq 'char *password;' "$source"
grep -Fq 'smbc_setOptionUserData(libsmbc->ctx, libsmbc);' "$source"
grep -Fq 'av_strlcpy(username, libsmbc->username, username_len);' "$source"
grep -Fq 'av_strlcpy(password, libsmbc->password, password_len);' "$source"
grep -Fq '"username", "set the username used for SMB authentication"' "$source"
grep -Fq '"password", "set the password used for SMB authentication"' "$source"
! grep -Eq 'av_(log|append_path_component).*password|smb://.*username|smb://.*password' "$source"
echo 'libsmbclient FFmpeg 8 credential patch test passed'
