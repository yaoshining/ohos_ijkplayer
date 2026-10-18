# Phase17 诊断 CI

本目录用于固定 mpv/libplacebo 源输入的两次不同绝对目录 fresh 交叉构建与静态验收。不是发布 workflow，不替换 Player/TV 的候选或库。

`inputs/bundles.json` 固定分片及完整压缩包摘要；bootstrap 严格校验后解包。输入包含公开组件源码/固定补丁、已 pin 的静态依赖、配套 FFmpeg 头与六库及 ABI 静态验收基线。`target-sdk` 仅含编译探测所需 API24 公共头和 Phase16 实际选中的目标库/CRT；没有整套 SDK 或 macOS 宿主程序。Linux 宿主工具另从 toolchain-lock.json 的官方 OpenHarmony 5.0 SDK 归档下载并校验。这是诊断混合工具链，不声称与 macOS 构建字节一致。

构建 recipe 使用 `/usr/local` 目标 prefix 与逐次独立 DESTDIR、相对 cross-file、编译期宏路径映射；FFmpeg 独立外部集合暂存于 mpv source/_staged/ffmpeg，使 Meson 原生生成稳定 `$ORIGIN` 构建 RPATH。不会安装到 runner /usr/local，也不后处理 ELF 路径。原始源码与额外 FFmpeg 文件独立校验，并检查精确集合。

`MPV_CONFDIR=/usr/local/etc/mpv` 与诊断字符串是本轮明确的配置变化，尚未真机验收。只比较同一平台、同一工具链的两次产物；历史依赖编译来源仍不完整，`fullyVerified=false`。既有 FFmpeg Python 目标路径修复保留。

workflow 运行门禁测试、两次 build/install/strip、真实库静态分析和完整 SHA/ELF/输入/配置比较。始终上传成功或失败证据；运行 URL/commit/平台与 artifact-index 用于独立回读。`formalArtifactAllowed=false`，设备播放/HDR/同步/生命周期效果待验收。
