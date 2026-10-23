# 场景矩阵

|场景|输入/实际链|接受条件|负例/失败|
|---|---|---|---|
|身份解析RED/GREEN|真实normal旧日志与新事件|稳定ID与owner代次完整|缺ID、query失败、地址复用、展示ID代替必须拒绝|
|A同consumer顺序|normal+TRACE、同mpv、force-window、至少三代 decoder / 三片、两次交接|同owner/image/consumer，旧drain+Destroy后新SetSurface，每片真实帧|owner重新创建或ID变化立即未通过|
|B真实并发|normal+TRACE+TEST、真实callback held与Close active等待、另外两请求线程|事件确认重叠；release后旧Destroy→新SetSurface；同consumer保持|仅sleep、同TID、无wait、无实际请求、提前绑定均拒绝|
|真实函数回归|真实oh_decode_admit/end/close、mpv父级/dispatch|normal/拒绝/失败/UNSAFE原策略保持|删除active等待、提前绑定变异被完整门禁拒绝|
|清理与运行身份|当前HAP/7库+实际PID|所有查询有效、PID/Ability/窗口消失、app保屏false或异常进程退出|Offline/timeout/残留窗口/错PID/陈旧JSON拒绝|
|CI|文本源码真实函数重放|精确clean SHA及Linux结果分别绑定|本轮只准备，未批准不push|

B屏障等待上限5秒，整场景上限120秒；任何失败记录不可改写成成功。平台GPU永久挂起未注入保持pending。A的证据不足不能由B测试侧锁补救。

## 实际结果与证据边界

A 的最低三代/两次交接由 A02 四代/三次交接覆盖。B 使用独立并发契约，load 请求可覆盖中间片，不要求所有请求都创建 decoder；每个实际创建 decoder 都须成功映射并按相邻生命周期核验。失败、错误 PID/TID、缺失字段、提前 release/SetSurface、owner 身份错误、任何 P30_APP failed 均拒绝。

CI 只重放宿主函数/观测/解析门禁；不重新执行设备或目标 SDK 构建。应用自有文本全部纳入新包，非文本资源只提交摘要；签名、媒体、HAP、动态库、SDK、凭据不上传。
