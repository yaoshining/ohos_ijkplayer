#!/usr/bin/env bash
set -euo pipefail
[ "${1:-}" = hx509-history ] && [ "$#" = 1 ] || { echo '必须显式选择 hx509-history' >&2; exit 2; }
root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd)
cd "$root"
export PYTHONDONTWRITEBYTECODE=1 LC_ALL=C TZ=UTC SOURCE_DATE_EPOCH=1755820644 PYTHONHASHSEED=1
source tools/ffmpeg8/ci-repo-env.sh
lock_git_repository "$root"
python3 -B -m unittest discover -s tools/hx509-history/tests -v
out="$root/out/phase10"
python3 -B tools/ffmpeg8/ci-prepare-inputs.py --output "$out/inputs"
mkdir -p "$out/downloads" "$out/generator-downloads"
python3 -B - "$out" <<'PY'
import hashlib,json,subprocess,sys
from pathlib import Path
out=Path(sys.argv[1])
for row in json.loads(Path('tools/ffmpeg8/dependency-sources.lock.json').read_text())['sources']:
    subprocess.run(['python3','-B','tools/ffmpeg8/fetch-sources.py','--name',row['name'],'--cache',str(out/'downloads')],check=True)
for row in json.loads(Path('tools/hx509-history/sources.lock.json').read_text())['sources']:
    p=out/'generator-downloads'/row['archiveFile']
    subprocess.run(['curl','-fL','--retry','3',row['url'],'-o',str(p)],check=True)
    if hashlib.sha256(p.read_bytes()).hexdigest()!=row['sha256']:raise ValueError('历史生成器来源摘要不符')
PY
cp -a /opt/host-provenance "$out/host-provenance"
python3 -B tools/hx509-history/run.py --profile hx509-history --output "$out/linux" --ndk "$out/inputs/ndk" --dependency-cache "$out/downloads" --generator-cache "$out/generator-downloads" --ffmpeg-repo "$out/inputs/ffmpeg" --builder-repo "$out/inputs/builder" --jobs 4
