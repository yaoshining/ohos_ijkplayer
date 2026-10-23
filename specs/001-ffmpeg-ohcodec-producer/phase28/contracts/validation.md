# 验证矩阵与证据要求

| 入口 | 场景 | 必须断言 |
|---|---|---|
| mapper_uninit / Vulkan mapper_release | held last_src，异步 release 未完成 | completion/归还先于最终引用与旧 Stop |
| vd_lavc reset/uninit + VO control | 无新帧、同 Surface 新旧 decoder、重复 Close | 同步 ack；旧 Stop 后新 SetSurface；无依赖下一帧 |
| vo current/queued + gpu-next queue | 旧帧重绘、mapper 同参数复用 | retire 后旧帧不能 remap；不误清其他 device |
| OHCodec 四 callback + Close/Flush | 在途 callback、同步 callback、上下文已 detach | ctx 访问受 gate；active 收敛；无锁反转 |
| create/init/start/cleanup | 各阶段失败及重复 cleanup | 仅清已初始化资源，无重复平台释放 |
| decode EOF/send_packet | 最后画面、重复 NULL、EOF 后新包 | EOF 不提前 Flush，新包前恰一次 drain+Flush |
| first_packet / fallback / reinit | 初始化 bootstrap、软硬切换、显式 seek | 所有破坏性调用进入审计，无 VO 依赖死锁 |
| Vulkan hold/signal/wait/release | hold/signal失败、release错误、完成未知 | 分类准确，无假 SAFE、重复 close FD、错误 fallback |
| 实验 watchdog | wait 永不返回、UI/worker停滞 | 外部超时终止唯一实验进程，日志保留 |
| GL / 软件 | EOF/seek/Close/切换 | NOT_APPLICABLE 无队列副作用，正常对照通过 |
| HDR / Python | Phase27全部已修复路径 | 真实源重新测试，不复用旧 green |
| 目标设备 | 单次Close、连续、seek、同Surface同参数切换 | decoder/window/epoch/buffer/fence事件、库/maps绑定 |

宿主 stub 只证明自有代码契约，不证明平台驱动行为。每条 RED 必须实际编译成功后出现语义失败；每条 GREEN 必须绑定 Phase28 真实函数和依赖。ASan/UBSan 与线程测试按可用性分别运行，缺口明确。设备所有正常路径 release 告警必须保留并判失败；不能只数日志是否消失。物理 HDR/主观声画未确认不升级。
