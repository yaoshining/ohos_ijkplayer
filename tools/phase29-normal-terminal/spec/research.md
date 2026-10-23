# 决策

选择独立mpv扩展ABI，不改核心客户端ABI版本。v1输入config以size/version校验，未来更大size接受已知前缀，保留字段必须为零；未知major拒绝。record snapshot限制写入当前已知大小并保留尾部canary。一次注册不可注销，宿主code/opaque寿命为进程寿命。

官方本地ApplicationContext文档：killAllProcesses仅主线程，Promise异步，异常应用终止时不保证完整生命周期。故只由独立app UI线程调用，不把terminateSelf当整个进程终止。3秒native deadline由应用层实现_Exit，仅诊断bundle，libmpv不退出。文档在evidence/application-context-doc.txt。

原app finish/recreate await active、前台无条件keepAwake不可用于终局；新路径必须绕开并封闭所有新任务。真实UI/保屏readback必须设备留证，缺失不冒充成功。
