# mpv OHCodec terminal 扩展 v1

mpv_ohcodec_terminal_api_version()返回独立扩展版本。register(config)复制handler与opaque值，不保留config指针；NULL/短size/未知version/非零reserved/NULLhandler失败，不消耗注册；成功一次后重复拒绝。enable()要求注册成功。snapshot(record)健康返回0，READY返回1，参数错误负值；不触碰mpv会话锁。

导出使用MPV_EXPORT，头支持C/C++，公共header安装；库内部handler适配在独立通知线程调用，固定record生命周期进程级。不得卸载/释放handler代码和opaque，无注销/重置。注册thread失败允许重试。未来更大的struct接受已知前缀并且不写未知尾部；ABI major必须为1，minor只接受支持版本。

应用不得在handler查询/stop/release mpv，必须使用缓存。新任务停止不能仅依赖owner gate，应在独立app native入口与UI入口统一拒绝。
