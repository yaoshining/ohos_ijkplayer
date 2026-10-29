# 状态

公共record：size、abi_version、platform_error、stage、owner_tag(uint64)、reserved[4]。config：size、abi_version、handler、opaque、reserved[4]。

应用adapter：UNREGISTERED→READY→TERMINAL；缓存record与最后进度；terminal首次时间由CLOCK_MONOTONIC确定，独立deadline使用它。UI接管结果分提示、保屏readback、kill-request；native-deadline与外部stop分开。
