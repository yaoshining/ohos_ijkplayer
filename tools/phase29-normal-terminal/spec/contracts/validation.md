# 验证门禁

公共ABI：NULL、短/大size、未知version、reserved、重复注册、失败重试、record有界写入、C/C++动态链接、实际目标导出。

应用：normal/SAFE_RELEASE_ERROR不退出且正常可再次播放；UNSAFE屏障父链保留，提示与保屏回读及UI kill-request，当前PID消失；callback挂起与UI阻塞分别由snapshot deadline退出，不能以外部force-stop冒充。无注册应在平台入口拒绝，不能自动fallback。注入macro/源差异/HAP身份单列。

全部证据保存精确输入SHA、退出码、失败日志；构建失败不算语义RED，device缺失则pending。

设备计时采用app/native单调时钟和系统hilog单调格式交叉核验，允许跨来源100ms量化/时钟偏差，deadline分支接受2.9–3.5秒；UI主动终止必须有ui1→ui2→ui3、实际截图、对应PID系统exit0且早于3秒。deadline分支要求对应PID exit86，不接受外部force-stop代替。外部清理只作残留检查。日志线程挂起时不要求伪造terminal-ready，使用已绑定源码/HAP、真实wait返回替换点及系统退出证据。
