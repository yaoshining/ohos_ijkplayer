# normal UNSAFE 公共接口与独立应用验证

正常构建新增4个mpv公共扩展接口，保留原54个接口。应用注册进程寿命接管器；首次UNSAFE锁存且保留完整父级链，通过独立线程通知。库不结束宿主进程。独立测试应用使用缓存进度，显示故障、关闭应用保屏并主动故障终止；原生3秒deadline不等待UI、callback或日志。用户需重新打开应用。异常终止不保证完整生命周期清理。

本目录是独立文本来源与宿主CI工具包，不是可发布候选或可直接签名的完整应用。`application`只保存应用自有源；SDK/FFmpeg/mpv安装头、7库、媒体、图标、签名均需从已锁定本地输入绑定，不随git上传。当前保留Player/TV只读，`formalArtifactAllowed=false`。

## 验证范围

`runner.py`要求clean精确提交，在checkout外输出。Linux工作流将实际运行公开ABI缺失RED3项/GREEN5项、真实normal父链23项、完整源码renderer提前释放负例、应用适配器5项、ArkTS真实保屏和UI方法、CI身份/收集门禁9项。TypeScript4.9.5由锁文件下载，禁用install scripts。目标ARM64构建和真机证据是独立本地结果，CI不冒充重复执行。

本地目标normal-e/f同SHA、目标4次C/C++强链接通过。真机正常库同PID双次真实EOF；测试返回替换变体验证Release安全清理/新producer拒绝、故障UI截图及exit0、callback/UI/logger阻塞exit86。详情见evidence-summary；完整原始记录仅本地封存，未上传。

旧构建a/b/c漏wrapper、d旧54符号门禁失败，旧采集无权限/日志丢失、开发runner失败均保留，未回写为通过。normal与故障变体HAP/源码宏分别绑定。

## 仍待验收

远端Linux CI（需批准精确SHA后推送）、实际Player/TV应用适配、真实GPU调用永不返回、强并发、物理HDR/主观声画。不替换候选库/HAR、不改系统设置。
