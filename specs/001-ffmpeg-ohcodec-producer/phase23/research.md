# Phase23 研究决策

决定：SMB先补服务器协议阶段及客户端smbc_open内部阶段；现有日志已越过FFmpeg/context初始化，但不足区分parse/connect/negotiate/auth/open。依据out/phase23/research/smb.md。该Samba支持1445，不能直接改端口猜根因；也不修改凭据/禁用安全校验碰运气。

决定：Vulkan按同Surface与新Surface分开量测热身和稳定期；NativeImage取得的window由NativeImage_Destroy释放，不能盲补DestroyNativeWindow。Phase22观察到每次Vulkan后ashmem/dmabuf各+1，但尚未唯一归因。

决定：GL验证GL-first、VK→GL、GL→VK→GL。Phase22旧format34为RGBA1010102、强制12为RGBA8888后恢复；这是跨API格式残留假设，尚需实验确认。修复若成立应在mpv GL选择EGLConfig后的格式匹配与恢复，不能全局强制RGBA8影响Vulkan/HDR。

来源层、工具链与重建入口由out/phase23/research/gpu.md补充。根另发现ohdec.c ref释放和分配失败路径风险，需要核实并回归；不把小块内存问题当fd增长根因。

这些是可证伪实验决策，根因作为实施阶段交付，不是未决定的需求。源码读取、设备试验、宿主回归和最终结论均独立；不扩大产品接线或发布范围。


## 已完成实验结论

SMB为夹具方言不兼容：SMB2最低2.1与Impacket2.0.2不相容；仅独立夹具采用SMB2_02，生产SMB库不变。06及最终10完成正/负例、断连和显式重新打开。

Vulkan为队列返回失败保留Acquire wrapper引用。07实际调用配对和目标库反汇编支撑根因；09仅换mpv后固定/新Surface各13轮稳定，最终双库10复验同样稳定。末10轮ashmem/dmabuf各1，等同无播放器对照。其他FFmpeg分配清理修复独立验证，不冒充句柄根因。

GL默认EGL native visual与窗口格式不匹配，即使fresh GL-first亦失败；来源层设置并恢复所选格式解决。最终11/12区分VK停止后GL恢复与真正GL主动停止。13另解决独立探针把vp当px的问题，读取实际XComponent px，不为接线错误修改播放器库。

来源、主机、目标与人类视听边界保持，详见版本化tools/phase23/README.md与evidence数字摘要。
