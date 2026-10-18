# Phase17 诊断 CI

本目录用于固定 mpv/libplacebo 源输入的两次不同绝对目录 fresh 交叉构建与静态验收。不是发布 workflow，不替换 Player/TV 的候选或库。

`inputs/bundles.json` 固定分片及完整压缩包摘要；bootstrap 严格校验后解包。输入包含公开组件源码/固定补丁、已 pin 的静态依赖、配套 FFmpeg 头与六库及 ABI 静态验收基线。`target-sdk` 仅含编译探测所需 API24 公共头和 Phase16 实际选中的目标库/CRT；没有整套 SDK 或 macOS 宿主程序。Linux 宿主工具另从 toolchain-lock.json 的官方 OpenHarmony 5.0 SDK 归档下载并校验。这是诊断混合工具链，不声称与 macOS 构建字节一致。

构建 recipe 使用 `/usr/local` 目标 prefix 与逐次独立 DESTDIR、相对 cross-file、编译期宏路径映射；FFmpeg 独立外部集合暂存于 mpv source/_staged/ffmpeg，使 Meson 原生生成稳定 `$ORIGIN` 构建 RPATH。不会安装到 runner /usr/local，也不后处理 ELF 路径。原始源码与额外 FFmpeg 文件独立校验，并检查精确集合。

`MPV_CONFDIR=/usr/local/etc/mpv` 与诊断字符串是本轮明确的配置变化，尚未真机验收。只比较同一平台、同一工具链的两次产物；历史依赖编译来源仍不完整，`fullyVerified=false`。既有 FFmpeg Python 目标路径修复保留。

workflow 运行门禁测试、两次 build/install/strip、真实库静态分析和完整 SHA/ELF/输入/配置比较。始终上传成功或失败证据；运行 URL/commit/平台与 artifact-index 用于独立回读。`formalArtifactAllowed=false`，设备播放/HDR/同步/生命周期效果待验收。

CI 初次因 PyPI 无 ninja==1.12.0 失败，现从官方发布下载并固定 ZIP/ELF 摘要与运行版本。第二次发现 configure executable probe 缺 Scrt1.o；目标包仅追加 API24 该启动对象（4648 bytes），旧包及失败证据保留。最终还按 Ninja 依赖记录对两次实际编译输入、生成文件、对象覆盖和 SHA 做独立比较；这是构建后字节与依赖日志绑定，不冒称编译时系统调用跟踪。

第三次 workflow 虽同平台重复性通过，独立回读发现 PL_HAVE_VK_PROC_ADDR 自动关闭：默认 clang++ 的 -lc++/-lc++abi 配置探测缺输入。保留这次结果并追加 API24 libc++.so 链接脚本及 libc++abi.a，不改源码/强制宏。bootstrap 增加实际 C++ Vulkan 链接探测且不执行 ARM64；summarize 要求生成配置中128个mpv HAVE_与11个libplacebo PL_HAVE_状态精确匹配已固定的本地双clean基线。
