# #12 x86_64 SMB 宿主运行时补交付

用户要求与失败证据：https://github.com/yaoshining/ohos_ijkplayer/issues/12#issuecomment-6898821057 。r2 六库审计成功，但消费者缺少 ohcodec_smb_runtime.h 和 ohcodec_smb_runtime_configure_v1，实际链接失败。本轮规格先于实现补齐。

## 合同

FR-01 复用 tools/phase20/apply.py 和 runtime 的真实 ARM64 Samba/FFmpeg 实现；不得使用恒成功 stub、环境变量替代或绕过初始化。
FR-02 公共结构和函数与 ARM64 逐字一致。配置字符串复制；NULL、结构大小错误、非法路径返回 -1/errno；相同配置幂等，冲突或首次 context 后配置返回 EBUSY；全局不可恢复失败保持 EIO。
FR-03 config/state/cache/resource 在 smbc_new_context 的原始实现前被原子发布。显式配置覆盖保留路径，禁止 HOME 回退。锁、context 计数及重入语义沿用真实实现。
FR-04 六库 x86_64 软件解码，导出 SMB 公共符号但无 av_ohcodec_* 硬解接口。头文件、pkg-config 和真实六库须完成独立消费者链接。
FR-05 完整新包与对应源码/补丁、源提交、实际宿主工具链、许可证/SBOM、manifest、包和各库 SHA-256 一并发布；保留旧附件，明确本地/CI 来源。
FR-06 回复 #12 下载与限制，只修改 ohos_ijkplayer。目标设备、SMB 服务端运行与低 API 兼容未执行则 pending。

## 验收

正常配置、字符串所有权、重复与冲突、非法参数、分配失败、初始化顺序及 context 生命周期均有回归。旧 SDK 缺头文件或符号时必须拒绝；真正重定位消费者链接成功。主机受控 backend 不声称真实目标 Samba 运行通过。
