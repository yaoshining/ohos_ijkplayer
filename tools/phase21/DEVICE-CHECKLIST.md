# 设备验收清单（全部待验收）

此包为独立native诊断，不是HAP或正式发布包。libplacebo已经静态纳入mpv。目录示例由准备器生成；在目标设备必须由受信任调用方按实际沙箱路径重新准备配置与资源。请勿使用包内记录的宿主绝对路径。不要直接替换Player/TV库。

- [ ] 目标动态加载器确实加载清单中的mpv与六库，平台库由设备提供；不得把SDK stub放入交付目录。
- [ ] 创建、销毁、重建、配置冲突/过晚、失败清理、目标目录权限。
- [ ] SMB登录、读取、seek、断线重连，网络凭据安全接入。
- [ ] OHCodec H264/HEVC硬解，GL/Vulkan首帧与持续渲染。
- [ ] 暂停/seek/flush/EOF/退出重播、Surface销毁重建。
- [ ] 目标字幕与OSD、实际CJK字体/emoji覆盖及资源投递；当前font1仅ASCII。
- [ ] 音视频同步、HDR/色彩、内存压力与异常释放。

hostSoftwareRender通过仅为Linux软件管线证据；targetExecuted=false、formalArtifactAllowed=false、deviceAcceptanceStatus=pending。
