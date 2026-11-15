# 状态与来源

公开 struct_size + 四个 const char* 与 phase20 相同；内部保存复制后的 input[4] 和派生 paths[11]，原子发布不可变值。未配置 → 已配置 → context started；显式失败进入 failed，生命周期计数控制 teardown，不提供 reset。

manifest 增加 smbRuntime 合同、头文件与 patch evidence 摘要、buildOrigin=local-source-build、buildHost/NDK/tools、producerCommit、完整 recipe 和源码包指针。设备状态仍 pending。
