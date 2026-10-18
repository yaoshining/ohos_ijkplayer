#!/usr/bin/env bash
# 独立诊断入口；不调用默认构建工作流。
set -euo pipefail
[ "${1:-}" = hx509-history ] && [ "$#" = 1 ] || { echo '必须显式选择 hx509-history' >&2; exit 2; }
root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd)
cd "$root"
docker build --platform linux/amd64 --pull -t hx509-history:locked -f tools/ffmpeg8/ci/Dockerfile tools/ffmpeg8/ci
out=out/phase10/container
[ ! -e "$out" ] || { echo '拒绝复用容器证据目录' >&2; exit 2; }
mkdir -p "$out"
image_id=$(docker image inspect hx509-history:locked --format '{{.Id}}')
docker image inspect "$image_id" > "$out/image-inspect.json"
docker create --cidfile "$out/container-id" --platform linux/amd64 --mount "type=bind,source=$root,target=/workspace" "$image_id" bash tools/hx509-history/ci-inside.sh hx509-history
container_id=$(cat "$out/container-id")
trap 'docker rm "$container_id" >/dev/null' EXIT
[ "$(docker inspect "$container_id" --format '{{.Image}}')" = "$image_id" ]
docker inspect "$container_id" > "$out/container-inspect.json"
sha256sum tools/ffmpeg8/ci/Dockerfile > "$out/dockerfile.sha256"
docker start -a "$container_id"
exit "$(docker inspect "$container_id" --format '{{.State.ExitCode}}')"
