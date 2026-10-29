#include <assert.h>
#include <stdio.h>
#include <string.h>
#include "libavcodec/avcodec.h"
#include "libavcodec/avcodec_internal.h"
#include "libavcodec/h2645_parse.h"
#include "libavcodec/h2645_sei.h"
#include "libavutil/intreadwrite.h"
#include "libavutil/mastering_display_metadata.h"
#include "libavutil/mem.h"

/* Fixture encoder only. Production unescape/parser/conversion are complete upstream objects. */
static size_t packet(uint8_t *out, unsigned type, const uint8_t *payload, size_t n) {
    uint8_t rbsp[256] = {0x4e, 0x01, 0, 0};
    rbsp[2] = type; rbsp[3] = n;
    memcpy(rbsp + 4, payload, n); rbsp[4 + n] = 0x80;
    out[0] = out[1] = out[2] = 0; out[3] = 1;
    size_t w = 4; unsigned zeros = 0;
    for (size_t i = 0; i < n + 5; i++) {
        if (zeros >= 2 && rbsp[i] <= 3) { out[w++] = 3; zeros = 0; }
        out[w++] = rbsp[i]; zeros = rbsp[i] ? 0 : zeros + 1;
    }
    return w;
}
static int parse(H2645SEI *sei, AVCodecContext *ctx, unsigned type, const uint8_t *payload, size_t n) {
    uint8_t bytes[512 + AV_INPUT_BUFFER_PADDING_SIZE] = {0};
    size_t size = packet(bytes, type, payload, n);
    H2645Packet pkt = {0};
    int rc = ff_h2645_packet_split(&pkt, bytes, size, ctx, 0, AV_CODEC_ID_HEVC, 0);
    assert(rc == 0 && pkt.nb_nals == 1 && pkt.nals[0].type == 39);
    H2645NAL *nal = &pkt.nals[0];
    assert(nal->size == (int)n + 5 && nal->data[2] == type && nal->data[3] == n);
    GetByteContext gbyte; GetBitContext gb;
    bytestream2_init(&gbyte, nal->data + 4, n);
    assert(init_get_bits8(&gb, nal->data + 4, n) == 0);
    rc = ff_h2645_sei_message_decode(sei, type, AV_CODEC_ID_HEVC, &gb, &gbyte, ctx);
    ff_h2645_packet_uninit(&pkt);
    return rc;
}
static void convert(AVFrame *frame, H2645SEI *sei, AVCodecContext *ctx) {
    H2645VUI vui = {0};
    assert(ff_h2645_sei_to_frame(frame, sei, AV_CODEC_ID_HEVC, ctx, &vui, 10, 10, 0) == 0);
}
int main(void) {
    AVCodecContext *ctx = avcodec_alloc_context3(NULL); assert(ctx);
    ctx->internal = ff_decode_internal_alloc(); assert(ctx->internal);
    const unsigned coords[8] = {13250,34500,7500,3000,34000,16000,15635,16450};
    uint8_t mdm[24] = {0}, cll[4] = {0};
    for (int i = 0; i < 8; ++i) AV_WB16(mdm + i * 2, coords[i]);
    AV_WB16(cll, 1000); AV_WB16(cll + 2, 400);
    for (int lum = 1000; lum <= 2000; lum += 1000) {
        AV_WB32(mdm + 16, lum * 10000); AV_WB32(mdm + 20, 50);
        H2645SEI sei = {0}; AVFrame *frame = av_frame_alloc(); assert(frame);
        assert(parse(&sei, ctx, SEI_TYPE_MASTERING_DISPLAY_COLOUR_VOLUME, mdm, sizeof(mdm)) == 0);
        assert(sei.mastering_display.present == 2 && !sei.content_light.present);
        convert(frame, &sei, ctx);
        AVFrameSideData *sd = av_frame_get_side_data(frame, AV_FRAME_DATA_MASTERING_DISPLAY_METADATA); assert(sd);
        AVMasteringDisplayMetadata *m = (void *)sd->data;
        assert(m->has_primaries && m->has_luminance);
        assert(m->max_luminance.num == lum * 10000 && m->max_luminance.den == 10000);
        assert(m->min_luminance.num == 50 && m->min_luminance.den == 10000);
        assert(m->display_primaries[0][0].num == 34000 && m->display_primaries[0][0].den == 50000);
        assert(m->display_primaries[1][0].num == 13250 && m->display_primaries[2][0].num == 7500);
        assert(m->white_point[0].num == 15635 && m->white_point[1].num == 16450);
        assert(!av_frame_get_side_data(frame, AV_FRAME_DATA_CONTENT_LIGHT_LEVEL));
        av_frame_free(&frame); ff_h2645_sei_reset(&sei);
    }
    {
        H2645SEI sei = {0}; AVFrame *frame = av_frame_alloc(); assert(frame);
        assert(parse(&sei, ctx, SEI_TYPE_CONTENT_LIGHT_LEVEL_INFO, cll, sizeof(cll)) == 0);
        assert(sei.content_light.present == 2 && !sei.mastering_display.present);
        convert(frame, &sei, ctx);
        AVFrameSideData *sd = av_frame_get_side_data(frame, AV_FRAME_DATA_CONTENT_LIGHT_LEVEL); assert(sd);
        AVContentLightMetadata *c = (void *)sd->data;
        assert(c->MaxCLL == 1000 && c->MaxFALL == 400);
        assert(!av_frame_get_side_data(frame, AV_FRAME_DATA_MASTERING_DISPLAY_METADATA));
        av_frame_free(&frame); ff_h2645_sei_reset(&sei);
    }
    {
        H2645SEI sei = {0};
        assert(parse(&sei, ctx, SEI_TYPE_MASTERING_DISPLAY_COLOUR_VOLUME, mdm, 23) == AVERROR_INVALIDDATA);
        assert(!sei.mastering_display.present);
        assert(parse(&sei, ctx, SEI_TYPE_CONTENT_LIGHT_LEVEL_INFO, cll, 3) == AVERROR_INVALIDDATA);
        assert(!sei.content_light.present);
        ff_h2645_sei_reset(&sei);
    }
    av_freep(&ctx->internal); avcodec_free_context(&ctx);
    puts("PASS real packet_split/message_decode/to_frame: MDM1000, MDM2000, independentCLL, truncatedMDM, truncatedCLL");
    return 0;
}
