# normal UNSAFE 公共接口与独立应用集成

用户已授权本阶段独立开发/目标构建/独立真机验证。维持提示故障后受控结束整个应用、由用户重开的选择。Player/TV 全目录只读，不替换候选，只用应用保屏，不改系统设置。旧464文件封存保持，formalArtifactAllowed=false。新提交必须精确预览后批准，当前不推送/不运行远端 CI。

公共扩展ABI具备显式版本/结构大小/保留字段校验、异步一次通知、进程寿命、不借用栈options；正常无故障不退出。目标构建采用既有API24 SDK和闭包输入，两次独立clean，正式normal无诊断/注入；测试注入变体单列。

独立应用将同步播放器工作留在native后台worker；UI通过adapter缓存读取终局，不能等待active Promise或调用mpv query/stop/release。terminal后run/recreate/stop/前台保屏开启全部拒绝。提示/关闭保屏后由应用主线程killAllProcesses；独立native deadline在首次snapshot3秒后结束本诊断进程，不等待UI或回调。外部force-stop仅清理，不能算接管通过。

实际GPU调用永不返回/物理HDR/强并发没有验证则pending。宿主、目标链接、HAP身份、设备UI与进程退出分别报告。
