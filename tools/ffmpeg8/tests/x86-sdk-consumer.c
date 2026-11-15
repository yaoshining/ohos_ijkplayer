/* 独立消费者：只使用安装后的公共头文件及六库，不使用 FFmpeg 源码目录。 */
#include <libavcodec/avcodec.h>
#include <libavformat/avformat.h>
#include <libavfilter/avfilter.h>
#include <libavutil/avutil.h>
#include <libswresample/swresample.h>
#include <libswscale/swscale.h>

int main(void)
{
    if ((avcodec_version() >> 16) != 62 || (avformat_version() >> 16) != 62 ||
        (avfilter_version() >> 16) != 11 || (avutil_version() >> 16) != 60 ||
        (swresample_version() >> 16) != 6 || (swscale_version() >> 16) != 9)
        return 1;
    return avformat_network_init() < 0;
}
