/* Native lifecycle probe. "software" explicitly requests a platform software
 * codec on emulators. Surface delivery here is offscreen. */
#include <inttypes.h>
#include <stdio.h>
#include <string.h>
#include <unistd.h>
#include <multimedia/player_framework/native_avcapability.h>
#include <native_image/native_image.h>
#include <native_window/external_window.h>
#include "libavcodec/avcodec.h"
#include "libavcodec/ohcodec_buffer.h"
#include "libavformat/avformat.h"
#include "libavutil/hwcontext.h"
#include "libavutil/hwcontext_oh.h"

#define CHECK(call) do { int rc_ = (call); if (rc_ < 0) { \
    fprintf(stderr, "%s: %s\n", #call, av_err2str(rc_)); exit(1); } } while (0)

static AVFrame *held;
static uint64_t previous_surface;
static void play(const char *file, const char *name, int first)
{
    AVFormatContext *in = NULL;
    CHECK(avformat_open_input(&in, file, NULL, NULL));
    CHECK(avformat_find_stream_info(in, NULL));
    int stream = av_find_best_stream(in, AVMEDIA_TYPE_VIDEO, -1, -1, NULL, 0);
    CHECK(stream);
    AVStream *video = in->streams[stream];
    const AVCodec *codec = avcodec_find_decoder_by_name("h264_ohcodec");
    AVCodecContext *ctx = avcodec_alloc_context3(codec);
    if (!ctx || video->codecpar->codec_id != AV_CODEC_ID_H264) exit(1);
    CHECK(avcodec_parameters_to_context(ctx, video->codecpar));
    ctx->pkt_timebase = video->time_base;
    OH_NativeImage *image = OH_ConsumerSurface_Create();
    if (!image) exit(2);
    OHNativeWindow *window = OH_NativeImage_AcquireNativeWindow(image);
    uint64_t id = 0;
    if (!window || OH_NativeWindow_GetSurfaceId(window, &id) || !id || id == previous_surface) exit(3);
    previous_surface = id;
    ctx->hw_device_ctx = av_hwdevice_ctx_alloc(AV_HWDEVICE_TYPE_OHCODEC);
    if (!ctx->hw_device_ctx) exit(4);
    AVHWDeviceContext *device = (void *)ctx->hw_device_ctx->data;
    ((AVOHCodecDeviceContext *)device->hwctx)->native_window = window;
    CHECK(av_hwdevice_ctx_init(ctx->hw_device_ctx));
    AVDictionary *opts = NULL;
    av_dict_set(&opts, "codec_name", name, 0);
    CHECK(avcodec_open2(ctx, codec, &opts));
    if (av_dict_count(opts)) exit(5);
    if (!first) {
        int stale = av_ohcodec_release_buffer((void *)held->data[3], 1);
        printf("old token render=%d expected=%d\n", stale, AVERROR(ESTALE));
        if (stale != AVERROR(ESTALE)) exit(6);
        av_frame_free(&held);
    }
    AVFrame *frame = av_frame_alloc();
    AVPacket *pkt = av_packet_alloc();
    if (!pkt || !frame) exit(7);
    int count = 0;
    while (count < 4) {
        if (!pkt->size) {
            CHECK(av_read_frame(in, pkt));
            if (pkt->stream_index != stream) { av_packet_unref(pkt); continue; }
        }
        int sent = avcodec_send_packet(ctx, pkt);
        if (sent != AVERROR(EAGAIN)) { CHECK(sent); av_packet_unref(pkt); }
        int got = avcodec_receive_frame(ctx, frame);
        if (got == AVERROR(EAGAIN)) continue;
        CHECK(got);
        if (frame->format != AV_PIX_FMT_OHCODEC) exit(8);
        if (first && count == 3) {
            held = av_frame_clone(frame);
            if (!held) exit(9);
        } else {
            CHECK(av_ohcodec_release_buffer((void *)frame->data[3], 1));
            OHNativeWindowBuffer *buf = NULL;
            int fence = -1;
            for (int i = 0; i < 100 && !buf; i++) {
                if (OH_NativeImage_AcquireNativeWindowBuffer(image, &buf, &fence)) {
                    buf = NULL;
                    usleep(5000);
                }
            }
            if (!buf || OH_NativeImage_ReleaseNativeWindowBuffer(image, buf, fence)) exit(10);
        }
        printf("pid=%d file=%s surface=%"PRIu64" frame=%d pts=%"PRId64" %s\n",
               getpid(), file, id, count, frame->pts, (first && count == 3) ? "held" : "acquired");
        av_frame_unref(frame);
        count++;
    }
    avcodec_free_context(&ctx);
    avformat_close_input(&in);
    av_frame_free(&frame);
    av_packet_free(&pkt);
    OH_NativeImage_Destroy(&image);
}

int main(int argc, char **argv)
{
    if (argc != 4 || (strcmp(argv[1], "hardware") && strcmp(argv[1], "software"))) return 64;
    setbuf(stdout, NULL);
    OH_AVCapability *cap = OH_AVCodec_GetCapabilityByCategory("video/avc", false,
                           !strcmp(argv[1], "hardware") ? HARDWARE : SOFTWARE);
    if (!cap) { fprintf(stderr, "no %s AVC capability\n", argv[1]); return 77; }
    const char *name = OH_AVCapability_GetName(cap);
    if (!name) return 77;
    printf("pid=%d platform=%s codec=%s\n", getpid(), argv[1], name);
    play(argv[2], name, 1);
    play(argv[3], name, 0);
    return 0;
}
