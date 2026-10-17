# 研究与证据

2026-10-17：现有 test-sdk-contract.sh 已通过。TV HEAD、HAR、HAR 内 libmpv 及六库均复核匹配用户基线。Player dist/ohcodec-diagnostics-20260923/delivery.json 的 HAR 是旧包，与当前 TV HAR 不同，只迁移六库/证据。八份 ~/.cache/vidall-player/smb-sysroot 静态库均匹配 smb-static-inputs.json。FFmpeg 与 libmpv-ohos-build 锁定提交本地可用；DevEco native NDK 可用。历史临时构建 prefix 不存在，不能把缓存普通 FFmpeg headers 冒充 OHCodec 原交付 headers。

这些检查发生于新增实现之前。现有源码/ijkplayer 改动保持不动。构建时源码归档自指定提交，不使用缓存工作树未提交内容。
