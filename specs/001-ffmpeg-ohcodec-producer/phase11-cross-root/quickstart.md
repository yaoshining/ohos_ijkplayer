# 验证顺序

1. 运行新增路径回归观察RED，最小实现后重跑；实际clang/pkg-config验证不同长度和空格输入，错误路径拒绝。
2. 真实FFmpeg configure检查稳定参数和实际依赖选择，禁止修改输出字符串。
3. 显式cross-root profile在两个fresh目录构建各自生成器/八库/六库，compare-sdks原始allMatch=true；跨NDK不比较相等。
4. 专用CI真实运行后按登记ZIP SHA下载复验全部pin/manifest/实际配置。任何失败保留日志。
5. 复核上轮索引及归档映射、TV组合和业务checkout/index，新阶段单独索引；真实设备pending。
