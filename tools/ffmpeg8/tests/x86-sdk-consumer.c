/* 独立消费者：只使用安装后的公共头文件及六库，不使用 FFmpeg 源码目录。 */
#include <libavcodec/avcodec.h>
#include <libavformat/avformat.h>
#include <libavformat/ohcodec_smb_runtime.h>
#include <libavfilter/avfilter.h>
#include <libavutil/avutil.h>
#include <libswresample/swresample.h>
#include <libswscale/swscale.h>

/* 链接探针不运行空路径配置；真实应用必须传入已准备的绝对路径。 */
int configure_smb(const struct ohcodec_smb_runtime_v1 *config)
{
    return ohcodec_smb_runtime_configure_v1(config);
}

int main(void)
{
    if ((avcodec_version() >> 16) != 62 || (avformat_version() >> 16) != 62 ||
        (avfilter_version() >> 16) != 11 || (avutil_version() >> 16) != 60 ||
        (swresample_version() >> 16) != 6 || (swscale_version() >> 16) != 9)
        return 1;
    return avformat_network_init() < 0;
}
