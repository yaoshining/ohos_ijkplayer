# SDK 消费合同

运行 `python3 tools/ffmpeg8/producer-sdk.py verify --sdk SDK_ROOT --manifest-sha256 PINNED_SHA256`；失败不得消费。库由 manifest.libraries 给出，不扫描任意缓存目录。status=runtime-ready 仅供 runtime 对齐；开发者必须检查 headers.status/pkgconfig.status 是否 ready。source-build 与 imported-baseline 互不替代。任何重建摘要差异只记录并报告，原基线 sdkRoot 不变。设备始终 pending。
