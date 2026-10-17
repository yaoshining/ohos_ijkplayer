#!/usr/bin/env bash
# 全新 CI checkout：依赖源码 → OHCodec 两次 clean → 审计 → 正式产物门禁。
set -euo pipefail
root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd)
cd "$root"
source tools/ffmpeg8/ci-repo-env.sh
lock_git_repository "$root"
out="$root/out/ci-ohcodec"
[ ! -e "$out" ] || { echo '拒绝复用已有 CI 工作目录' >&2; exit 2; }
mkdir -p "$out"
python3 tools/ffmpeg8/ci-prepare-inputs.py --output "$out/inputs"
export OHOS_NDK="$out/inputs/ndk"
export JOBS=${JOBS:-4}
export LC_ALL=C TZ=UTC SOURCE_DATE_EPOCH=1755820644 PYTHONHASHSEED=1
export SOURCE_CACHE="$out/dependencies/downloads"
mkdir -p "$SOURCE_CACHE" "$out/dependency-recipe"
cp tools/ffmpeg8/{build-libsmbclient.sh,fetch-sources.py,dependency-sources.lock.json,dependency-paths.py,generator-lock.py,verify-dependency-features.py,elf-audit.py,samba-target-config.py} "$out/dependency-recipe/"
python3 - "$SOURCE_CACHE" <<'PYFETCH'
import json,subprocess,sys
from pathlib import Path
for row in json.loads(Path('tools/ffmpeg8/dependency-sources.lock.json').read_text())['sources']:
    subprocess.run(['python3','tools/ffmpeg8/fetch-sources.py','--name',row['name'],'--cache',sys.argv[1]],check=True)
PYFETCH
cp -a /opt/host-provenance "$out/host-provenance"
python3 tools/ffmpeg8/host-lock.py capture --ndk "$OHOS_NDK" --recipe "$out/dependency-recipe" --profile linux-debian-bookworm-20250204 --output "$out/host-lock.json"
for iteration in a b; do
  python3 tools/ffmpeg8/run-dependency-build.py --root "$out/dependencies/$iteration" --recipe "$out/dependency-recipe" --host-lock "$out/host-lock.json" --cache "$SOURCE_CACHE" --ndk "$OHOS_NDK" --jobs "$JOBS"
  python3 tools/ffmpeg8/dependency-manifest.py --work "$out/dependencies/$iteration/work" --sysroot "$out/dependencies/$iteration/sysroot" --cache "$SOURCE_CACHE" --ndk "$OHOS_NDK" --recipe "$out/dependency-recipe"
done
python3 tools/ffmpeg8/dependency-repeat.py --first "$out/dependencies/a/sysroot" --second "$out/dependencies/b/sysroot" --require-build-records --report "$out/static-repeat.json"
PREFIX="$out/dependencies/a/sysroot"
python3 tools/ffmpeg8/new-source-closure.py --first "$PREFIX" --second "$out/dependencies/b/sysroot" --repeat "$out/static-repeat.json" --host-lock "$out/host-lock.json" --container "$root/out/ci-container" --host-provenance "$out/host-provenance" --output "$PREFIX/new-source-closure.json"
dep_manifest="$PREFIX/dependency-manifest-closed.json"
dep_sha=$(sha256sum "$dep_manifest" | awk '{print $1}')
for iteration in a b; do
  python3 tools/ffmpeg8/producer-sdk.py build \
    --ndk "$OHOS_NDK" --smb "$PREFIX" --static-manifest "$dep_manifest" --static-manifest-sha256 "$dep_sha" \
    --ffmpeg-repo "$out/inputs/ffmpeg" --builder-repo "$out/inputs/builder" \
    --delivery "$root/tools/ffmpeg8/baseline-evidence" --output "$out/clean-$iteration" --jobs "$JOBS" \
    > "$out/clean-$iteration.log" 2>&1
  manifest="$out/clean-$iteration/work/prefix/manifest.json"
  python3 tools/ffmpeg8/producer-sdk.py verify --sdk "$(dirname "$manifest")" --manifest-sha256 "$(sha256sum "$manifest" | awk '{print $1}')"
done
python3 tools/ffmpeg8/compare-sdks.py --first "$out/clean-a/work/prefix" --second "$out/clean-b/work/prefix" --report "$out/reproducibility.json"
# 此命令预期在闭包证据不完整时失败；禁止 continue-on-error 或用普通 build.sh 替代。
python3 tools/ffmpeg8/ci-gate.py --manifest "$out/clean-a/work/prefix/manifest.json" --repeat "$out/reproducibility.json" --inputs "$out/inputs/input-verification.json" --report "$out/formal-gate.json" --manifest-sha256 "$(sha256sum "$out/clean-a/work/prefix/manifest.json" | awk '{print $1}')" --second-sdk "$out/clean-b/work/prefix" --second-manifest-sha256 "$(sha256sum "$out/clean-b/work/prefix/manifest.json" | awk '{print $1}')" --input-root "$out/inputs" --verification-only
