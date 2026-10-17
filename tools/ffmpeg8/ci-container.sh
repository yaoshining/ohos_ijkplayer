#!/usr/bin/env bash
# 只在 Linux Docker runner 上运行。容器 ID 与实际 image ID 在启动前校验。
set -euo pipefail
root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd)
cd "$root"
mkdir -p out/ci-container
image_tag=ohcodec-host:locked
docker build --platform linux/amd64 --pull -t "$image_tag" -f tools/ffmpeg8/ci/Dockerfile tools/ffmpeg8/ci
image_id=$(docker image inspect "$image_tag" --format '{{.Id}}')
docker image inspect "$image_id" > out/ci-container/image-inspect.json
docker create --cidfile out/ci-container/container-id --platform linux/amd64 \
  --mount "type=bind,source=$root,target=/workspace" "$image_id" bash tools/ffmpeg8/ci-build-ohcodec.sh
container_id=$(cat out/ci-container/container-id)
trap 'docker rm "$container_id" >/dev/null' EXIT
actual_image=$(docker inspect "$container_id" --format '{{.Image}}')
[ "$actual_image" = "$image_id" ] || { echo '容器 image 身份不符' >&2; exit 1; }
docker inspect "$container_id" > out/ci-container/container-inspect.json
sha256sum tools/ffmpeg8/ci/Dockerfile > out/ci-container/dockerfile.sha256
docker start -a "$container_id"
code=$(docker inspect "$container_id" --format '{{.State.ExitCode}}')
exit "$code"
