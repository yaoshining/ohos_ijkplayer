#!/usr/bin/env bash
# End-to-end SMB protocol test.  Run on the target/device with an FFmpeg 8
# protocol test client that accepts `-protocol_opts key=value` arguments.
set -euo pipefail
client=${FFMPEG8_SMB_TEST_CLIENT:?set FFMPEG8_SMB_TEST_CLIENT to the target test client}
server=${SMB_TEST_SERVER:-127.0.0.1}
share=${SMB_TEST_SHARE:-media}
path=${SMB_TEST_PATH:-sample.txt}
user=${SMB_TEST_USER:-ffmpegtest}
password=${SMB_TEST_PASSWORD:-ffmpeg-test-password}
workgroup=${SMB_TEST_WORKGROUP:-WORKGROUP}
url="smb://${server}/${share}/${path}"
secret_marker="${SMB_TEST_SECRET_MARKER:-$password}"
run() { "$client" "$@" 2>&1; }

# Anonymous share must open without injecting credentials.
anonymous_log=$(run --url "$url" --protocol_opts "workgroup=$workgroup")
printf '%s\n' "$anonymous_log" | grep -Fq "$secret_marker" && { echo 'secret leaked in anonymous log' >&2; exit 1; }

# Authenticated share receives credentials exclusively through protocol options.
auth_log=$(run --url "$url" --protocol_opts "username=$user,password=$password,workgroup=$workgroup")
printf '%s\n' "$auth_log" | grep -Fq "$secret_marker" && { echo 'secret leaked in authenticated log' >&2; exit 1; }
printf '%s\n' "$url" | grep -Fq '@' && { echo 'credentials leaked into URL' >&2; exit 1; }

# A deliberately invalid credential set must fail and still remain redacted.
invalid_log_file=$(mktemp "${TMPDIR:-/tmp}/ffmpeg8-smb-invalid.XXXXXX")
trap 'rm -f "$invalid_log_file"' EXIT
if run --url "$url" --protocol_opts "username=invalid,password=$password" >"$invalid_log_file" 2>&1; then
    echo 'invalid SMB credentials unexpectedly succeeded' >&2
    exit 1
fi
invalid_log=$(<"$invalid_log_file")
printf '%s\n' "$invalid_log" | grep -Fq "$secret_marker" && { echo 'secret leaked in failure log' >&2; exit 1; }
echo 'SMB anonymous/authentication/redaction tests passed'
