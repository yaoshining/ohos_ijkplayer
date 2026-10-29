# Phase23 最小修复与证据

本阶段只修改独立复制来源和诊断工程。旧候选、Player/TV 及 Phase22 封存保持不变；正式产物资格不在本阶段授予。

## SMB

生产库未发现需要改动的 SMB 逻辑。夹具 Impacket 0.13.0 只提供 SMB 2.0.2，而 Samba 的配置 `SMB2` 最低实际为 2.1。独立诊断配置改成 `SMB2_02`，生产默认策略不变。

06 实验的 URL 与 AVOptions 两条路径均验证：错误认证 -13，正确认证 0，8 MiB 全量 SHA 与六段 seek 一致；缺文件 -2，关闭端口 -111；服务端主动断连后读取 -103，显式重新打开 0 并再次完成全量与 seek。不声称透明重连。服务器 NTSTATUS 数字事件用于判断认证阶段，不能仅凭回调布尔值。

证据在 `experiments/smb-matrix-06`。断连夹具仅对指定测试文件触发一次 socket shutdown，真实 socketpair 回归覆盖重复触发及其他文件不受影响。

## Vulkan

03 固定 Surface 和 08 新 Surface 各 13 轮旧实现均持续增长：每轮留下一个 ashmem 与 dmabuf，等待销毁后 3 秒仍存在。软件 Vulkan 对照没有相同持续增长。

07 直接日志记录 905 次 Acquire/Release、30 次 import 创建/销毁与 3 次 image 创建/销毁；每轮最后一次 Release 返回 41210000（BUFFER_NOT_IN_CACHE），其余返回 0。目标 libnative_image.so 的实际释放函数反汇编显示：队列 ReleaseBuffer 失败后跳过 wrapper 的 Unreference。官方固定提交的源码提供相同参考行为，但不据此声称它是该固件的准确来源。

最小补丁保持额外 wrapper 引用直到 Release 返回；失败时补释放 Acquire 引用，随后释放额外引用。fence 根据 API 合同由系统接管，失败路径不能再次 close。另修复 pltex 已创建而 ra_tex 包装分配失败时的清理，正常 ra_tex_free 路径不重复销毁 pltex。

真实源码函数注入成功/失败返回进行 RED/GREEN；句柄回归另用固定与新 Surface 各 3 轮热身、10 轮观测验证。稳定句柄数量不等于证明所有内存均无泄漏，fdinfo 无访问权限也不能被记为零。

## 默认 OpenGL

默认 EGLConfig 的 native visual 为 RGBX8888（11），原窗口格式为 RGBA8888（12），原实现未同步窗口格式。独立库在创建 EGL surface 前读取 EGL_NATIVE_VISUAL_ID，保存并设置窗口格式；按 EGL surface/context 销毁顺序恢复原格式，然后释放窗口。

不强制所有格式为 RGBA8，也不让普通播放应用代设格式。真实 init/uninit 函数的 80 组回归覆盖查询、设置、surface/context 初始化失败及恢复失败后二次初始化。05 设备实验默认 GL 硬/软解及 VK→GL 已出现实际帧、seek、EOF，最终组合仍需完整复验。

## FFmpeg 生命周期

仅修改复制来源的 ohdec.c：正常释放 decoder 引用对象；创建失败释放 decoder/ref；硬件 frame 包装早期失败时按 generation 归还 output；av_buffer_ref 失败不再解引用 NULL。18 组实际函数回归覆盖正常、分配失败与过期 generation。

两个新 FFmpeg source/build 目录六库字节一致，264 个复用静态依赖和三份源码结束复核一致。这是使用锁定静态依赖的 FFmpeg fresh build，不是重新引导所有依赖。最终上机组合只替换 avcodec 与 mpv，其余五库继续采用 Phase21 输入，并通过目标 maps 再次核验。

## 交付边界

CI 仅收必要源码、补丁、测试、数字摘要及脱敏证据。HAP、签名、凭据、系统二进制和设备私有原件留在本地。主机单元回归、目标构建、目标执行、人工视听分别报告；人工听音与物理声画同步仍待验收。


## 最终组合及补充验收

最终组合仅替换 mpv `da6fcbc59b743d1afdaead29cbdf4d3994646f371d6b9202aa7295d958c5aaf9` 与 avcodec `6f541583c4dd1ff3e4e5472404809340b4594a790e66917bfec4bbd40844e4dd`；其他五库为 Phase21 输入，目标 maps 已逐个校验。10 实验36场景全部完成，其中固定/新 Surface 各13轮稳定期 ashmem/dmabuf 各1，与无播放器对照相同，总FD采样均59。固定稳定期RSS为226776–254864 KiB，新Surface为226136–256804 KiB，未据此声称所有内存分配无泄漏。

11 实验验证 Vulkan 主动停止后新 Surface GL H264/软件/HEVC恢复；12 实验独立验证 GL H264 硬解和软件解码分别主动停止、销毁后新 Surface 恢复。停止场景预期 stopped=1/eof=0；之后正常场景仍要求实际帧、seek、EOF。

截图审查发现诊断工程把960×540 vp布局数值当成播放器px，导致GL viewport偏小。13实验改用XComponentController.getXComponentSurfaceRect()，日志显示实际传参及NativeWindow GET_BUFFER_GEOMETRY均2880×1620 px；这只修改探针，未修改播放器库。修正后GL/Vulkan截图填满相同区域。截图仅核对画面与字形，不替代人工视听或色彩准确性验收。
