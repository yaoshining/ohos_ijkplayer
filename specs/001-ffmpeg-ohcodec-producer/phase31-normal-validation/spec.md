# Phase31 正常构建真实播放验收

## 用户范围
独立测试工程验证指定 NAS 长播、成功 seek、切换影片/片源（“切片”，不是 HLS 分段生产）、暂停恢复、前后台和关闭重开。Player/TV 全目录只读，不替换候选/HAR/SDK，不改系统设置，仅应用保屏。新 SHA 推送前给精确预览。formalArtifactAllowed=false。

## 功能要求
- FR01 身份：复用 Phase30 A 正常控制流 TRACE-only mpv/FFmpeg 配套组合，TEST/DIAGNOSTIC/EXPERIMENT/RETURN_REPLACEMENT 关闭；保留 terminal 公共接口与接管。新 HAP 内全部9库摘要、目标进程7库、源/编译输入一致。与 TV imported-baseline 哈希不同属已知独立组合，不替换它。
- FR02 NAS：只读指定 nas-media-01；凭据仅从用户指定0600文件由程序读取，设备私有派生配置不进HAP/CI，结束覆盖清零并核验。禁止发布私人路径/原始mpv NAS日志。
- FR03 连续长播：先短冒烟再独立60分钟长播，从首次有效视频样本计3600s；1x、OHCodec+Vulkan、无seek/load/暂停/前后台/重启/提前EOF，采样间隔目标5s，最大gap<=15s，持续video-pts推进且media/wall差<=10s；样本和心跳覆盖完整。任何中断失败，不能跨运行拼时长。
- FR04 成功 seek：单独操作场景，先稳定播放，实际mpv seek absolute+exact返回0，后有SEEK及PLAYBACK_RESTART；调用后最多15s内SEEK/PLAYBACK_RESTART及目标有效样本齐备，操作场景每100ms采样；目标30s附近首个有效观测误差<=2s，之后至少3s视频进度推进；另反向seek到5s同标准。命令0或-12都不能单独当seek成功。
- FR05 暂停恢复：实际pause=true返回0且属性回读true，连续>=3s播放位置变动<=0.25s；resume返回0且回读false，随后>=3s视频PTS推进；查询失败不充作0。
- FR06 切换片源：独立短媒体pq→hlg→sdr经loadfile切换，每代FILE_LOADED+PLAYBACK_RESTART+至少3s视频推进，旧END_FILE STOP属于明确切换而非静默忽略；实际3代加载，不能把被覆盖请求计成功。
- FR07 前后台：独立会话稳定播放后实际Home进入后台>=3s再回到同Ability；绑定同PID/session，UIAbility background/foreground与窗口/Stage事件、恢复后PTS推进和保屏readback。后台音视频连续性不作默认要求。回前台15s内必须出现foreground和恢复焦点、有效视频位置，随后推进>=3s；同PID/session/播放器实例，期间没有新FILE_LOADED或SurfaceDestroy才判原会话恢复PASS。若Surface销毁/重新load，仅另记重建结果，原会话恢复PENDING。
- FR08 关闭重开分两项：①正常mpv destroy、保屏false、session_end后应用terminateSelf；30s内有效Ability/Window查询确认消失，重新进入有新Ability/session实例且再次播放推进，允许OS缓存同PID，明确称“正常Ability关闭重开”。②在正常清理后外部force-stop、严格旧PID/Ability/window消失查询、新PID重开播放，单列“外部终止后冷重开”；不得当自然进程退出。killAllProcesses不替代正常退出。
- FR09 测试：真实新策略/实际调用切片正常、边界、失败先RED后GREEN；门禁反例包含缺样本、命令0但未跳转、pause未冻结、错误代次、缺前后台事件、旧PID/查询失败、来源漂移。采样器/分析器测试夹具不是设备证据。
- FR10 边界和发布：旧封存不变，新结果新路径；只读远端，准备纯文本CI包+clean精确重放+SHA预览，不推送。物理HDR/主观声画、真实GPU永久挂起、多实例并发继续待验收。

## 成功标准
SC01 上述每个场景独立 PASS/FAIL/PENDING，原始时间/返回码/身份可追溯；不可用总体绿灯掩盖单项失败。
SC02 每次运行有正常保屏解除或独立失败清理证据；设备连接查询必须有效，空stdout不单独证明进程消失。
SC03 资源只报告观测趋势，不能称无泄漏。历史52分钟gap根因仍 unresolved。
SC04 构建/设备/宿主CI分别声明，不追认历史来源，也不把本地macOS重放当远端Linux。

暂停稳定窗口要求连续有效pause=true样本且间隔<=0.5s；false、查询失效、间隔超限或单调时间倒退直接失败，不跨缺口累计暂停时长。
