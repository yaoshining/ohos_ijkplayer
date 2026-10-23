# 事件与身份

事件：module、PID、实际TID、模块内原子递增seq、CLOCK_MONOTONIC时间、op、ownerInstance/consumerGeneration、decoderInstance/tokenGeneration、consumerSurfaceId、NativeImage/NativeWindow指针、query rc、平台rc。

ownerInstance和decoderInstance各DSO独立单调且不复用，不把两个DSO的seq当同一全局序；通过PID/consumerSurfaceId和实际调用返回、测试屏障关系建立跨模块顺序。generation只随真实owner创建增加。指针仅辅助，不单独认定身份。

测试状态：DISARMED→ARMED→CALLBACK_HELD→REAL_CLOSE_WAIT→REQUESTS_ENTERED→RELEASED→COMPLETED。每一步必须有可核对真实事件，超时记失败/未覆盖，不补写假事件。进程外watchdog只兜底，不冒充应用自行清理。
