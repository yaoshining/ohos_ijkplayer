# 构建和消费

OHOS_ARCH=x86_64 OHOS_NDK=<Native> JOBS=8 bash tools/ffmpeg8/build.sh

SDK 安装头文件 libavformat/ohcodec_smb_runtime.h。应用须先准备真实、规范化的绝对路径及 state/private、state/state、state/lock，然后在创建任何 SMB context 前调用 configure_v1。不能把链接探针中的空参数作为运行配置。

运行测试与真实目标运行分开报告；SDK 继续不提供 OHCodec 硬解。
