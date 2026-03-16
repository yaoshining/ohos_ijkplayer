/*
 * ffpipenode_ohos_mediacodec_vdec.cpp
 *
 * Copyright (C) 2024 Huawei Device Co.,Ltd.
 *
 * This file is part of ijkPlayer.
 *
 * ijkPlayer is free software; you can redistribute it and/or
 * modify it under the terms of the GNU Lesser General Public
 * License as published by the Free Software Foundation; either
 * version 2.1 of the License, or (at your option) any later version.
 *
 * ijkPlayer is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
 * Lesser General Public License for more details.
 *
 * You should have received a copy of the GNU Lesser General Public
 * License along with ijkPlayer; if not, write to the Free Software
 * Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA
 */

#include "ffpipenode_ohos_mediacodec_vdec.h"

#include <chrono>
#include <unistd.h>
#include "libswscale/swscale.h"
#include "ohos_video_decoder_data.h"
#include "ohos_video_decoder.h"
#include "deviceinfo.h"

static const int NS_TO_US = 1000;
static const int MILLISECOND = 7;
static const int SUPPORT_NATIVE_BUFFER_FORMAT_SDK_VERSION = 22;
extern const char *OH_MD_KEY_VIDEO_NATIVE_BUFFER_FORMAT __attribute__((weak));

class IJKFF_Pipenode_Opaque {
public:
    IJKFF_Pipeline *pipeline;
    FormatInfo formatInfoEntry;
    CodecData codecData;
    VideoDecoder decoder;
    FFPlayer *ffp;
    AVCodecParameters *codecpar;
    AVPacket *pkt;
    SDL_Vout *weakVout;
    OhosVideoCodecWrapper *codecWrapper {nullptr};
    const AVBitStreamFilter *aVBitStreamFilter {nullptr};
    AVBSFContext *avbsfContext {nullptr};
    std::atomic_int64_t frameCount {0};
    void DecoderInput(AVPacket pkt);
    bool DecoderOutput(AVFrame *frame);
    bool TryGetDecoderOutput(AVFrame *frame);
    void DropDecoderOutput();
    std::atomic<bool> inputThreadExit;
};

struct AVBSFInternal {
    AVPacket *buffer_pkt;
    int eof;
};

static void func_destroy(IJKFF_Pipenode *node)
{
    IJKFF_Pipenode_Opaque *opaque = static_cast<IJKFF_Pipenode_Opaque *>(node->opaque);
    if (opaque->codecWrapper) {
        delete opaque->codecWrapper;
        opaque->codecWrapper = nullptr;
    }
    opaque->decoder.Release();
}
void IJKFF_Pipenode_Opaque::DecoderInput(AVPacket pkt)
{
    int32_t ret = 0;
    int inputTime = 30;
    CodecBufferInfo codecBufferInfo;
    codecBufferInfo.buff_ = OH_AVBuffer_Create(pkt.size);
    auto bufferAddr = OH_AVBuffer_GetAddr(codecBufferInfo.buff_);
    memcpy(bufferAddr, pkt.data, pkt.size);
    codecBufferInfo.attr.size = pkt.size;
    codecBufferInfo.attr.pts = pkt.pts;
    if (pkt.flags == 1) {
        codecBufferInfo.attr.flags = AVCODEC_BUFFER_FLAGS_CODEC_DATA|AVCODEC_BUFFER_FLAGS_SYNC_FRAME;
    } else {
        codecBufferInfo.attr.flags = AVCODEC_BUFFER_FLAGS_NONE;
    }

    ret = this->codecData.InputData(codecBufferInfo, std::chrono::milliseconds(inputTime));
    if (ret == 0) {
        this->decoder.PushInputData(codecBufferInfo);
    }
    OH_AVBuffer_Destroy(codecBufferInfo.buff_);
}

void IJKFF_Pipenode_Opaque::DropDecoderOutput()
{
    CodecBufferInfo codecBufferInfoReceive;
    this->codecData.DropOutputBuffer(codecBufferInfoReceive);
    this->decoder.FreeOutputData(codecBufferInfoReceive.bufferIndex);
}

int32_t GetFormatInfo(OH_AVFormat *format, FormatType type)
{
    int result = 0;

    const char * const formatKeys[FORMAT_TYPE_NBR] = {
        OH_MD_KEY_VIDEO_PIC_WIDTH,
        OH_MD_KEY_VIDEO_PIC_HEIGHT,
        OH_MD_KEY_VIDEO_STRIDE,
        OH_MD_KEY_VIDEO_SLICE_HEIGHT,
        OH_MD_KEY_PIXEL_FORMAT,
        OH_MD_KEY_VIDEO_CROP_TOP,
        OH_MD_KEY_VIDEO_CROP_BOTTOM,
        OH_MD_KEY_VIDEO_CROP_LEFT,
        OH_MD_KEY_VIDEO_CROP_RIGHT,
        OH_MD_KEY_WIDTH,
        OH_MD_KEY_HEIGHT,
    };

    bool ret = OH_AVFormat_GetIntValue(format, formatKeys[type], &result);
    
    return ret ? result : -1;
}

static void ff_mediacodec_buffer_copy_nv21(OhosVideoCodecWrapper *codecWrapper,
                                           uint8_t *data,
                                           AVFrame *frame)
{
    int i;
    uint8_t *src = nullptr;
    OhosVideoCodecWrapper *codec = codecWrapper;
    for (i = DATA_NUM_0; i < DATA_NUM_2; i++) {
        int height;

        src = data;
        if (i == 0) {
            height = codec->display_height;
        } else if (i == 1) {
            height = codec->display_height / DATA_NUM_2;
            src += codec->crop_top * codec->stride;
            src += codec->slice_height * codec->stride;
            src += codec->crop_left;
        }

        if (frame->linesize[i] == codec->stride) {
            memcpy(frame->data[i], src, height * codec->stride);
        } else {
            int j = DATA_NUM_0;
            int width = DATA_NUM_0;
            uint8_t *dst = frame->data[i];

            if (i == DATA_NUM_0) {
                width = codec->display_width;
            } else if (i == DATA_NUM_1) {
                width = FFMIN(frame->linesize[i], FFALIGN(codec->display_width, DATA_NUM_2));
            }
            for (j = DATA_NUM_0; j < height; j++) {
                memcpy(dst, src, width);
                src += codec->stride;
                dst += frame->linesize[i];
            }
        }
    }
}

static void CheckParamsAndInitConfig(OhosVideoCodecWrapper *codecWrapper, AVFrame *frame,
                                     int *displayWidth, int *displayHeight)
{
    LOGI("CheckParamsAndInitConfig start\n");
    // Validate pixel format
    if (frame->format != AV_PIX_FMT_P010LE) {
        LOGE("ERROR: Wrong pixel format: %d, expected P010LE (%d)\n",
             frame->format, AV_PIX_FMT_P010LE);
        *displayWidth = -1;
        *displayHeight = -1;
        return;
    }

    OhosVideoCodecWrapper *codec = codecWrapper;
    // Basic non-null parameter validation
    if (!codec || !frame || !frame->data[0]) {
        LOGE("ERROR: Invalid parameter\n");
        *displayWidth = -1;
        *displayHeight = -1;
        return;
    }

    // Initialize display width and height (after cropping)
    if (codec->display_width > 0 && codec->display_height > 0) {
        *displayWidth = codec->display_width;
        *displayHeight = codec->display_height;
    } else {
        *displayWidth = codec->width - codec->crop_left - codec->crop_right;
        *displayHeight = codec->height - codec->crop_top - codec->crop_bottom;
    }

    // Ensure width and height are at least 1
    *displayWidth = FFMAX(1, *displayWidth);
    *displayHeight = FFMAX(1, *displayHeight);
    const int bytesPerPixel = 2; // P010LE: 2 bytes per pixel

    // Calibrate display width based on frame linesize
    if (frame->linesize[0] > 0) {
        int widthFromLinesize = frame->linesize[0] / bytesPerPixel;
        if (widthFromLinesize > 0 && widthFromLinesize != *displayWidth) {
            LOGW("WARNING: Adjusting display_width from %d to %d (trusting frame linesize)\n",
                 *displayWidth, widthFromLinesize);
            *displayWidth = widthFromLinesize;
        }
    }
}

static int CheckFrameBufferValidity(AVFrame *frame, int displayWidth, int displayHeight)
{
    LOGI("CheckFrameBufferValidity start\n");
    if (!frame) {
        LOGE("ERROR:frame is null!\n");
        return -1;
    }
    const int bytesPerPixel = 2;
    // Check buffer reference and size for each plane
    for (int i = 0; i < DATA_NUM_2; i++) {
        if (!frame->data[i]) {
            LOGE("ERROR: frame->data[%d] is NULL\n", i);
            return -1;
        }
        if (frame->buf[i]) {
            // Calculate required buffer size for current plane
            size_t neededSize;
            if (i == 0) {
                neededSize = displayHeight * frame->linesize[0];
            } else {
                neededSize = (displayHeight / DATA_NUM_2) * frame->linesize[1];
            }

            if (frame->buf[i]->size < neededSize) {
                LOGE("ERROR: Plane %d buffer too small! %zu < %zu\n", i, frame->buf[i]->size, neededSize);
                return -1;
            }
        } else {
            LOGW("WARNING: Plane %d has no buffer reference\n", i);
        }
    }

    // Validate display parameter validity
    if (displayWidth <= 0 || displayHeight <= 0) {
        LOGE("ERROR: invalid display size: %dx%d\n", displayWidth, displayHeight);
        return -1;
    }

    return 0;
}

static void CopyYPlaneData(OhosVideoCodecWrapper *codecWrapper, uint8_t *data, AVFrame *frame,
                           int displayWidth, int displayHeight)
{
    LOGI("CopyYPlaneData start\n");
    const int bytesPerPixel = 2;
    OhosVideoCodecWrapper *codec = codecWrapper;
    uint8_t *srcY = data;
    uint8_t *dstY = frame->data[0];

    // Calculate stride in bytes (get from codecWrapper directly)
    int strideBytes = codec->stride;
    int minRequiredBytes = displayWidth * bytesPerPixel;
    if (strideBytes < minRequiredBytes) {
        LOGW("WARNING: stride %d < min_required %d, treating as pixel unit\n",
             strideBytes, minRequiredBytes);
        strideBytes = codec->stride * bytesPerPixel;
    }

    // Apply Y plane crop offset
    int yStartOffset = codec->crop_top * strideBytes + codec->crop_left * bytesPerPixel;
    srcY += yStartOffset;

    int dstYStride = frame->linesize[0];
    int copyYBytes = displayWidth * bytesPerPixel;
    // Limit copy bytes to not exceed destination/source stride
    copyYBytes = FFMIN(copyYBytes, dstYStride);
    copyYBytes = FFMIN(copyYBytes, strideBytes - codec->crop_left * bytesPerPixel);
    if (copyYBytes <= 0 || displayHeight <= 0) {
        LOGE("ERROR: invalid Y copy parameters\n");
        return;
    }

    // Copy Y plane data line by line
    size_t ySrcNeeded = displayHeight * strideBytes;
    for (int y = 0; y < displayHeight; y++) {
        memcpy(dstY, srcY, copyYBytes);
        srcY += strideBytes;
        dstY += dstYStride;
    }
}

static void CopyUVPlaneData(OhosVideoCodecWrapper *codecWrapper, uint8_t *data, AVFrame *frame,
                            int displayWidth, int displayHeight)
{
    OhosVideoCodecWrapper *codec = codecWrapper;
    const int bytesPerPixel = 2;
    if (!frame || !codec) {
        LOGE("ERROR: frame or codec is null!\n");
        return;
    }

    int strideBytes = codec->stride;
    int minRequiredBytes = displayWidth * bytesPerPixel;
    if (strideBytes < minRequiredBytes) {
        LOGW("WARNING: stride %d < min_required %d, treating as pixel unit\n",
             strideBytes, minRequiredBytes);
        strideBytes = codec->stride * bytesPerPixel;
    }
    size_t yPlaneSize;
    if (codec->slice_height > 0) {
        yPlaneSize = codec->slice_height * strideBytes;
    } else {
        yPlaneSize = codec->height * strideBytes;
    }
    uint8_t *srcUv = data + yPlaneSize;
    if (!frame || !frame->data[1]) {
        LOGE("ERROR: frame or frame->data[1] is null!\n");
        return;
    }
    uint8_t *dstUv = frame->data[1];
    if (!dstUv) {
        LOGE("ERROR: UV destination is NULL\n");
        return;
    }

    int dstUvStride = frame->linesize[1];
    int uvHeight = displayHeight / 2;
    int cropTopUv = codec->crop_top / 2;
    int cropLeftUv = codec->crop_left;
    srcUv += cropTopUv * strideBytes;
    srcUv += cropLeftUv * bytesPerPixel;
    int copyUvBytes = displayWidth * bytesPerPixel;
    copyUvBytes = FFMIN(copyUvBytes, dstUvStride);
    copyUvBytes = FFMIN(copyUvBytes, strideBytes - cropLeftUv * bytesPerPixel);
    if (copyUvBytes <= 0 || uvHeight <= 0) {
        LOGE("ERROR: invalid UV copy parameters\n");
        return;
    }
    for (int y = 0; y < uvHeight; y++) {
        memcpy(dstUv, srcUv, copyUvBytes);
        srcUv += strideBytes;
        dstUv += dstUvStride;
    }
}

static void ff_mediacodec_buffer_copy_p010(OhosVideoCodecWrapper *codecWrapper,
                                           uint8_t *data, AVFrame *frame)
{
    LOGI("ff_mediacodec_buffer_copy_p010 start\n");
    // Initialize configuration parameters (remove strideBytes)
    int displayWidth = 0;
    int displayHeight = 0;
    CheckParamsAndInitConfig(codecWrapper, frame, &displayWidth, &displayHeight);
    if (displayWidth <= 0 || displayHeight <= 0) {
        return;
    }

    // Validate buffer validity
    if (CheckFrameBufferValidity(frame, displayWidth, displayHeight) != 0) {
        return;
    }

    // Copy Y plane data (5 params)
    CopyYPlaneData(codecWrapper, data, frame, displayWidth, displayHeight);

    // Copy UV plane data (5 params)
    CopyUVPlaneData(codecWrapper, data, frame, displayWidth, displayHeight);
}

static int GetPixFormat(OH_AVFormat *format, OhosVideoCodecWrapper* codecWrapper)
{
    int pixelFormat[] = {AV_PIX_FMT_NONE, AV_PIX_FMT_YUV420P, AV_PIX_FMT_NV12, AV_PIX_FMT_NV21};
    int pixformat = AV_PIX_FMT_NONE;
    codecWrapper->color_format = GetFormatInfo(format, FormatType::FORMAT_TYPE_PIXEL_FORMAT);
    int videoNativeBufferFormat = -1;
    int apiVersion = OH_GetSdkApiVersion();
    LOGI("Current SDK API version: %d", apiVersion);
    if (apiVersion >= SUPPORT_NATIVE_BUFFER_FORMAT_SDK_VERSION) {
        if (OH_MD_KEY_VIDEO_NATIVE_BUFFER_FORMAT != nullptr) {
            bool ret = OH_AVFormat_GetIntValue(format, OH_MD_KEY_VIDEO_NATIVE_BUFFER_FORMAT, &videoNativeBufferFormat);
            if (!ret) {
                LOGE("ERROR: get video native buffer format fail!");
            }
        }
    }
    if (videoNativeBufferFormat == NATIVEBUFFER_PIXEL_FMT_YCBCR_P010) {
        codecWrapper->color_format = videoNativeBufferFormat;
        pixformat = AV_PIX_FMT_P010LE;
    } else if (codecWrapper->color_format < sizeof(pixelFormat) / sizeof(pixelFormat[0])) {
        pixformat = pixelFormat[codecWrapper->color_format];
    } else {
        LOGE("Error: color_format exceeds pixelFormat array size\n");
        return pixformat;
    }
    return pixformat;
}

static int qsvenc_get_continuous_buffer(AVFrame *frame, OH_AVFormat *format, CodecBufferInfo*  codecBufferInfoReceive,
                                        OhosVideoCodecWrapper* codecWrapper)
{
    codecWrapper->width = GetFormatInfo(format, FormatType::FORMAT_TYPE_IMAGE_WIDTH);
    codecWrapper->height = GetFormatInfo(format, FormatType::FORMAT_TYPE_IMAGE_HEIGHT);
    codecWrapper->stride = GetFormatInfo(format, FormatType::FORMAT_TYPE_VIDEO_STRIDE);
    codecWrapper->slice_height = GetFormatInfo(format, FormatType::FORMAT_TYPE_SLICE_HEIGHT);
    codecWrapper->crop_top = GetFormatInfo(format, FormatType::FORMAT_TYPE_CROP_TOP);
    codecWrapper->crop_bottom = GetFormatInfo(format, FormatType::FORMAT_TYPE_CROP_BOTTOM);
    codecWrapper->crop_left = GetFormatInfo(format, FormatType::FORMAT_TYPE_CROP_LEFT);
    codecWrapper->crop_right = GetFormatInfo(format, FormatType::FORMAT_TYPE_CROP_RIGHT);
    codecWrapper->display_width = GetFormatInfo(format, FormatType::FORMAT_TYPE_VIDEO_WIDTH);
    codecWrapper->display_height = GetFormatInfo(format, FormatType::FORMAT_TYPE_VIDEO_HEIGHT);
    codecWrapper->color_format = GetFormatInfo(format, FormatType::FORMAT_TYPE_PIXEL_FORMAT);

    uint8_t *bufferAddr = OH_AVBuffer_GetAddr(codecBufferInfoReceive->buff_);
    frame->format = GetPixFormat(format, codecWrapper);
    frame->pts = codecBufferInfoReceive->attr.pts;
    frame->pkt_dts = codecBufferInfoReceive->attr.pts;
    frame->width = codecWrapper->width;
    frame->height = codecWrapper->height;
    
    int ret = av_frame_get_buffer(frame, 64);
    if (ret < 0) {
        LOGE("Could not allocate frame data\n");
        return -1;
    }
    switch (frame->format) {
        case AV_PIX_FMT_NV12:
        case AV_PIX_FMT_NV21:
            ff_mediacodec_buffer_copy_nv21(codecWrapper, bufferAddr, frame);
            break;
        case AV_PIX_FMT_YUV420P:
            break;
        case AV_PIX_FMT_RGBA:
            break;
        case AV_PIX_FMT_P010LE:
            ff_mediacodec_buffer_copy_p010(codecWrapper, bufferAddr, frame);
            break;
        default:
            LOGE("frame->format failed  = %d\n", frame->format);
            break;
    }
    return 0;
}

int Nv12ToYuv420p(AVFrame *&yuv420p_frame, AVFrame *&nv12_frame, int width, int height)
{
    yuv420p_frame = av_frame_alloc();
    if (!yuv420p_frame) {
        LOGE("nv12_to_yuv420p yuv420p_frame av_frame_alloc failed");
        return -1;
    }
    yuv420p_frame->format = AV_PIX_FMT_YUV420P;
    yuv420p_frame->width = width;
    yuv420p_frame->height = height;
    av_image_alloc(yuv420p_frame->data, yuv420p_frame->linesize, width, height, AV_PIX_FMT_YUV420P, 1);
    struct SwsContext *swsCtx =
        sws_getContext(width, height, AV_PIX_FMT_NV12, width, height, AV_PIX_FMT_YUV420P, 0, nullptr, nullptr, nullptr);
    if (!swsCtx) {
        av_frame_free(&yuv420p_frame);
        LOGE("nv12_to_yuv420p sws_ctx null");
        return -1;
    }
    sws_scale(swsCtx, nv12_frame->data, nv12_frame->linesize, 0, height, yuv420p_frame->data, yuv420p_frame->linesize);
    sws_freeContext(swsCtx);
    return 0;
}

int P010LEToYuv420p(AVFrame *&yuv420p_frame, AVFrame *&p010le_frame, int width, int height)
{
    if (!p010le_frame) {
        LOGE("ERROR: P010LEToYuv420p ERROR: Input frame is NULL!\n");
        return -1;
    }

    if (!p010le_frame->data[0] || !p010le_frame->data[1]) {
        LOGE("ERROR: P010LEToYuv420p ERROR: Input frame has NULL data pointers!\n");
        return -1;
    }

    LOGI("P010LEToYuv420p start\n");
    yuv420p_frame = av_frame_alloc();
    if (!yuv420p_frame) {
        LOGE("ERROR: p010le_to_yuv420p av_frame_alloc failed!");
        return -1;
    }
    yuv420p_frame->format = AV_PIX_FMT_YUV420P;
    yuv420p_frame->width = width;
    yuv420p_frame->height = height;

    int ret = av_image_alloc(yuv420p_frame->data, yuv420p_frame->linesize, width, height, AV_PIX_FMT_YUV420P, 1);
    if (ret < 0) {
        LOGE("ERROR: p010le_to_yuv420p av_image_alloc failed, ret=%d", ret);
        av_frame_free(&yuv420p_frame);
        return -1;
    }

    struct SwsContext *swsCtx = sws_getContext(width, height, AV_PIX_FMT_P010LE, width, height, AV_PIX_FMT_YUV420P,
        SWS_BILINEAR, nullptr, nullptr, nullptr);
    if (!swsCtx) {
        LOGE("ERROR: p010le_to_yuv420p sws_getContext failed!");
        av_freep(yuv420p_frame->data);
        av_frame_free(&yuv420p_frame);
        return -1;
    }
    int result = sws_scale(swsCtx, p010le_frame->data, p010le_frame->linesize, 0, height,
        yuv420p_frame->data, yuv420p_frame->linesize);
    if (result != height) {
        LOGW("WARNING: sws_scale converted %d lines, expected %d\n", result, height);
    }
    sws_freeContext(swsCtx);
    return 0;
}

static int CheckRecordParamsAndStatus(FFPlayer *ffp, AVFrame *frame)
{
    int isValid = 0;
    if (!ffp || !frame) {
        LOGE("ERROR: RecordMediaCodecVideoFrame invalid parameter!\n");
        return isValid;
    }

    if (frame->width <= 0 || frame->height <= 0) {
        LOGE("ERROR: RecordMediaCodecVideoFrame invalid frame dimensions!\n");
        return isValid;
    }

    if (ffp->record_write_data.isInRecord != OHOS_RECORD_STATUS_ON ||
        !ffp->record_write_data.recordFramesQueue) {
        return isValid;
    }

    if (!frame->data[0] || !frame->data[1]) {
        LOGE("ERROR: frame has NULL data pointers!\n");
        return isValid;
    }

    isValid = 1;
    return isValid;
}

static int ConvertFrameToYuv420p(AVFrame *frame, AVFrame **yuv420pFrame)
{
    *yuv420pFrame = nullptr;
    int result = -1;

    if (frame->format == AV_PIX_FMT_NV12) {
        result = Nv12ToYuv420p(*yuv420pFrame, frame, frame->width, frame->height);
    } else if (frame->format == AV_PIX_FMT_P010LE) {
        result = P010LEToYuv420p(*yuv420pFrame, frame, frame->width, frame->height);
    } else {
        LOGE("record unsupport video format: %d", frame->format);
        return -1;
    }

    if (result < 0 || !*yuv420pFrame) {
        LOGE("ERROR: record format convert failed, result=%d", result);
        return -1;
    }
    if (!(*yuv420pFrame)->data[DATA_NUM_0] || !(*yuv420pFrame)->data[DATA_NUM_1] ||
        !(*yuv420pFrame)->data[DATA_NUM_2]) {
        LOGE("ERROR: YUV420P frame has NULL data pointers!\n");
        av_freep((*yuv420pFrame)->data);
        av_frame_free(yuv420pFrame);
        return -1;
    }
    return 0;
}

static int AllocRecordFrameData(AVFrame *yuv420pFrame, RecordFrameData *frData)
{
    // Calculate size for each plane
    size_t ySize = (size_t)yuv420pFrame->linesize[DATA_NUM_0] * yuv420pFrame->height;
    size_t uSize = (size_t)yuv420pFrame->linesize[DATA_NUM_1] * yuv420pFrame->height / DATA_NUM_2;
    size_t vSize = (size_t)yuv420pFrame->linesize[DATA_NUM_2] * yuv420pFrame->height / DATA_NUM_2;

    // Initialize record frame data structure
    frData->pts = yuv420pFrame->pts;
    frData->data0 = (uint8_t *)malloc(ySize);
    if (!frData->data0) {
        LOGE("ERROR: Memory allocation failed for data0!\n");
        return -1;
    }
    frData->data1 = (uint8_t *)malloc(uSize);
    if (!frData->data1) {
        LOGE("ERROR: Memory allocation failed for data1!\n");
        free(frData->data0);
        return -1;
    }
    frData->data2 = (uint8_t *)malloc(vSize);
    if (!frData->data2) {
        LOGE("ERROR: Memory allocation failed for data2!\n");
        free(frData->data0);
        free(frData->data1);
        return -1;
    }

    // Set record frame metadata
    frData->dataNum = FRAME_DATA_NUM_3;
    frData->frameType = OHOS_FRAME_TYPE_VIDEO;
    frData->lineSize0 = yuv420pFrame->linesize[DATA_NUM_0];
    frData->lineSize1 = yuv420pFrame->linesize[DATA_NUM_1];
    frData->lineSize2 = yuv420pFrame->linesize[DATA_NUM_2];
    frData->format = AV_PIX_FMT_YUV420P;
    frData->writeFileStatus = DATA_NUM_0;

    return 0;
}

static int CheckBufferAndCopyData(AVFrame *yuv420pFrame, RecordFrameData *frData)
{
    // Validate Y plane buffer size
    if (yuv420pFrame->buf[DATA_NUM_0]) {
        size_t yBufferSize = yuv420pFrame->buf[DATA_NUM_0]->size;
        size_t yNeededSize = (size_t)yuv420pFrame->linesize[DATA_NUM_0] * yuv420pFrame->height;
        if (yBufferSize < yNeededSize) {
            LOGE("ERROR: Y plane buffer too small! Buffer:%zu, Needed:%zu\n", yBufferSize, yNeededSize);
            return -1;
        }
    }
    // Validate U plane buffer size
    if (yuv420pFrame->buf[DATA_NUM_1]) {
        size_t uBufferSize = yuv420pFrame->buf[DATA_NUM_1]->size;
        size_t uNeededSize = (size_t)yuv420pFrame->linesize[DATA_NUM_1] * yuv420pFrame->height / DATA_NUM_2;
        if (uBufferSize < uNeededSize) {
            LOGE("ERROR: U plane buffer too small! Buffer:%zu, Needed:%zu\n", uBufferSize, uNeededSize);
            return -1;
        }
    }
    // Validate V plane buffer size
    if (yuv420pFrame->buf[DATA_NUM_2]) {
        size_t vBufferSize = yuv420pFrame->buf[DATA_NUM_2]->size;
        size_t vNeededSize = (size_t)yuv420pFrame->linesize[DATA_NUM_2] * yuv420pFrame->height / DATA_NUM_2;
        if (vBufferSize < vNeededSize) {
            LOGE("ERROR: V plane buffer too small! Buffer:%zu, Needed:%zu\n", vBufferSize, vNeededSize);
            return -1;
        }
    }
    // Copy Y/U/V plane data
    size_t ySize = (size_t)yuv420pFrame->linesize[DATA_NUM_0] * yuv420pFrame->height;
    size_t uSize = (size_t)yuv420pFrame->linesize[DATA_NUM_1] * yuv420pFrame->height / DATA_NUM_2;
    size_t vSize = (size_t)yuv420pFrame->linesize[DATA_NUM_2] * yuv420pFrame->height / DATA_NUM_2;

    if (yuv420pFrame->data[DATA_NUM_0]) memcpy(frData->data0, yuv420pFrame->data[DATA_NUM_0], ySize);
    if (yuv420pFrame->data[DATA_NUM_1]) memcpy(frData->data1, yuv420pFrame->data[DATA_NUM_1], uSize);
    if (yuv420pFrame->data[DATA_NUM_2]) memcpy(frData->data2, yuv420pFrame->data[DATA_NUM_2], vSize);

    return 0;
}

void RecordMediaCodecVideoFrame(FFPlayer *ffp, AVFrame *frame)
{
    int isValid = CheckRecordParamsAndStatus(ffp, frame);
    if (!isValid) {
        return;
    }
    AVFrame *yuv420pFrame = nullptr;
    RecordFrameData frData = {0};

    if (ConvertFrameToYuv420p(frame, &yuv420pFrame) < 0) {
        return;
    }

    if (AllocRecordFrameData(yuv420pFrame, &frData) < 0) {
        av_freep(yuv420pFrame->data);
        av_frame_free(&yuv420pFrame);
        return;
    }

    if (CheckBufferAndCopyData(yuv420pFrame, &frData) < 0) {
        free(frData.data0);
        free(frData.data1);
        free(frData.data2);
        av_freep(yuv420pFrame->data);
        av_frame_free(&yuv420pFrame);
        return;
    }

    if (!ffp->record_write_data.recordFramesQueue) {
        LOGE("ERROR: recordFramesQueue is NULL!\n");
        av_freep(yuv420pFrame->data);
        av_frame_free(&yuv420pFrame);
        free(frData.data0);
        free(frData.data1);
        free(frData.data2);
        return;
    }

    int writeIndex = ffp->record_write_data.windex;
    ffp->record_write_data.recordFramesQueue[writeIndex] = frData;
    ffp->record_write_data.windex += DATA_NUM_1;

    ffp->record_write_data.srcFormat.height = yuv420pFrame->height;
    ffp->record_write_data.srcFormat.width = yuv420pFrame->width;

    av_freep(yuv420pFrame->data);
    av_frame_free(&yuv420pFrame);
}

bool IJKFF_Pipenode_Opaque::DecoderOutput(AVFrame *frame)
{
    CodecBufferInfo codecBufferInfoReceive;
    OhosVideoCodecWrapper *codec = this->codecWrapper;
    bool ret = false;
    ret = this->codecData.OutputData(codecBufferInfoReceive);
    if (!ret) {
        return false;
    }
    OH_AVBuffer_GetBufferAttr(codecBufferInfoReceive.buff_, &codecBufferInfoReceive.attr);
    OH_AVFormat *format = OH_VideoDecoder_GetOutputDescription(this->decoder.decoder_);
    if (qsvenc_get_continuous_buffer(frame, format, &codecBufferInfoReceive, codec) < 0) {
        OH_AVBuffer_Destroy(codecBufferInfoReceive.buff_);
        OH_AVFormat_Destroy(format);
        return false;
    }
    OH_AVFormat_Destroy(format);
    this->decoder.FreeOutputData(codecBufferInfoReceive.bufferIndex);
    OH_AVBuffer_Destroy(codecBufferInfoReceive.buff_);
    if (codecBufferInfoReceive.attr.flags == AVCODEC_BUFFER_FLAGS_EOS) {
        this->codecData.ShutDown();
    }
    if (ffp->is_screenshot) {
        AVFrame *yuv420p_frame;
        int result = -1;
        if (frame->format == AV_PIX_FMT_NV12) {
            result = Nv12ToYuv420p(yuv420p_frame, frame, frame->width, frame->height);
        } else if (frame->format == AV_PIX_FMT_P010LE) {
            result = P010LEToYuv420p(yuv420p_frame, frame, frame->width, frame->height);
        } else {
            LOGE("screenshot unsupport format: %d", frame->format);
            return false;
        }
        if (result < 0) {
            return false;
        }
        ffp->is_screenshot = 0;
        SaveCurrentFramePicture(yuv420p_frame, ffp->screen_file_name);
        free(ffp->screen_file_name);
        av_freep(yuv420p_frame->data);
        av_frame_free(&yuv420p_frame);
        ffp->screen_file_name = NULL;
    }
    RecordMediaCodecVideoFrame(ffp, frame);
    return true;
}

bool IJKFF_Pipenode_Opaque::TryGetDecoderOutput(AVFrame *frame)
{
    CodecBufferInfo codecBufferInfoReceive;
    OhosVideoCodecWrapper *codec = this->codecWrapper;
    bool ret = false;
    ret = this->codecData.TryGetOutputBuffer(codecBufferInfoReceive);
    if (!ret) {
        return false;
    }
    OH_AVBuffer_GetBufferAttr(codecBufferInfoReceive.buff_, &codecBufferInfoReceive.attr);
    frame->pts = codecBufferInfoReceive.attr.pts;
    frame->pkt_dts = codecBufferInfoReceive.attr.pts;
    return true;
}

static bool try_get_video_frame(FFPlayer *ffp, Decoder *d, AVFrame *frame, IJKFF_Pipenode_Opaque *opaque)
{
    bool gotPicture = false;
    if ((gotPicture = opaque->TryGetDecoderOutput(frame)) == false) {
        return false;
    }
    return true;
}

static int decoder_decode_push_data(FFPlayer *ffp, IJKFF_Pipenode_Opaque *opaque)
{
    Decoder *d = &(ffp->is->viddec);
    while (opaque->inputThreadExit) {
        bool gotPkt = true;
        if (opaque->codecData.HasInputBuffer()) {
            AVPacket pkt;
            AVFormatContext* fmt_ctx = ffp->is->ic;
            do {
                if (d->queue->nb_packets == 0) {
                    SDL_CondSignal(d->empty_queue_cond);
                }
                if (ffp_packet_queue_get_or_buffering(ffp, d->queue, &pkt, &d->pkt_serial, &d->finished) < 0) {
                    LOGE("ffp_packet_queue_get_or_buffering failed");
                    opaque->inputThreadExit = false;
                    gotPkt = false;
                    return -1;
                }
                if (ffp_is_flush_packet(&pkt)) {
                    d->finished = 0;
                    d->next_pts = d->start_pts;
                    d->next_pts_tb = d->start_pts_tb;
                }
            } while (d->queue->serial != d->pkt_serial);
    
            int bsfRret = av_bsf_send_packet(opaque->avbsfContext, &pkt);
            if (bsfRret < 0) {
                AVBSFInternal *tmp_internal = (AVBSFInternal *)opaque->avbsfContext->internal;
                if (opaque->avbsfContext && tmp_internal->eof) {
                    tmp_internal->eof = 0;
                    av_packet_unref(tmp_internal->buffer_pkt);
                    bsfRret = av_bsf_send_packet(opaque->avbsfContext, &pkt);
                    if (bsfRret < 0) {
                        LOGE("av_bsf_send_packet retry failed %d", bsfRret);
                        gotPkt = false;
                    }
                } else {
                    LOGE("av_bsf_send_packet failed %d", bsfRret);
                    gotPkt = false;
                }
            }
            while (bsfRret >= 0) {
                bsfRret = av_bsf_receive_packet(opaque->avbsfContext, &pkt);
                if (bsfRret == AVERROR_EOF) {
                    d->finished = d->pkt_serial;
                    avcodec_flush_buffers(d->avctx);
                    av_packet_unref(&pkt);
                    LOGE("av_bsf_receive_packet failed");
                    gotPkt = false;
                }
            }
            if (gotPkt) {
                opaque->DecoderInput(pkt);
                av_packet_unref(&pkt);
            }
        }
        usleep(1 * NS_TO_US);
    }

    return 0;
}

void drop_video_frame(IJKFF_Pipenode_Opaque *opaque)
{
    if (opaque) {
        opaque->DropDecoderOutput();
    }
}

static int decoder_decode_ohos_frame(FFPlayer *ffp, Decoder *d, AVFrame *frame, IJKFF_Pipenode_Opaque *opaque)
{
    int gotPicture = -1;
    if (opaque->DecoderOutput(frame)) {
        gotPicture = 1;
    }
    return gotPicture;
}

static int get_video_frame(FFPlayer *ffp, AVFrame *frame, IJKFF_Pipenode_Opaque *opaque)
{
    VideoState *is = ffp->is;
    if (is == nullptr) {
        return -1;
    }
    int gotPicture = 0;

    ffp_video_statistic_l(ffp);
    if (try_get_video_frame(ffp, &is->viddec, frame, opaque)) {
        double dpts = NAN;
        if (frame->pts != AV_NOPTS_VALUE)
            dpts = av_q2d(is->video_st->time_base) * frame->pts;

        frame->sample_aspect_ratio = av_guess_sample_aspect_ratio(is->ic, is->video_st, frame);

        if (ffp->framedrop>0 || (ffp->framedrop && ffp_get_master_sync_type(is) != AV_SYNC_VIDEO_MASTER)) {
            ffp->stat.decode_frame_count++;
            if (frame->pts != AV_NOPTS_VALUE) {
                double diff = dpts - ffp_get_master_clock(is);
                if (!isnan(diff) && fabs(diff) < AV_NOSYNC_THRESHOLD &&
                    diff - is->frame_last_filter_delay < 0 &&
                    is->viddec.pkt_serial == is->vidclk.serial &&
                    is->videoq.nb_packets) {
                    is->frame_drops_early++;
                    is->continuous_frame_drops_early++;
                    if (is->continuous_frame_drops_early > ffp->framedrop) {
                        gotPicture = decoder_decode_ohos_frame(ffp, &is->viddec, frame, opaque);
                        is->continuous_frame_drops_early = 0;
                    } else {
                        ffp->stat.drop_frame_count++;
                        if (ffp->stat.decode_frame_count > 0) {
                            ffp->stat.drop_frame_rate = static_cast<float>(ffp->stat.drop_frame_count) /
                                static_cast<float>(ffp->stat.decode_frame_count);
                        }
                        drop_video_frame(opaque);
                        gotPicture = 0;
                    }
                } else {
                    gotPicture = decoder_decode_ohos_frame(ffp, &is->viddec, frame, opaque);
                }
            } else if (is->continuous_frame_drops_early <= ffp->framedrop) {
                ffp->stat.drop_frame_count++;
                if (ffp->stat.decode_frame_count > 0) {
                    ffp->stat.drop_frame_rate = static_cast<float>(ffp->stat.drop_frame_count) /
                        static_cast<float>(ffp->stat.decode_frame_count);
                }
                drop_video_frame(opaque);
                gotPicture = 0;
            }
        } else {
            gotPicture = decoder_decode_ohos_frame(ffp, &is->viddec, frame, opaque);
        }
    }
    return gotPicture;
}

static int ffplay_video_ohos_thread(FFPlayer *ffp, IJKFF_Pipenode_Opaque *opaque)
{
    VideoState *is = ffp->is;
    AVFrame *frame = av_frame_alloc();
    frame->format = AV_PIX_FMT_NONE;
    double pts;
    double duration;
    int ret;
    AVRational tb = is->video_st->time_base;
    AVRational frameRate = av_guess_frame_rate(is->ic, is->video_st, NULL);
    int64_t dstPts = -1;
    int64_t lastPts = -1;
    int retryConvertImage = 0;
    int convertFrameCount = 0;
    int interval = 1000;

    ffp_notify_msg2(ffp, FFP_MSG_VIDEO_ROTATION_CHANGED, ffp_get_video_rotate_degrees(ffp));

    if (!frame) {
        return AVERROR(ENOMEM);
    }

    opaque->inputThreadExit = true;
    std::thread pushInputThread(decoder_decode_push_data, ffp, opaque);
    
    for (;;) {
        ret = get_video_frame(ffp, frame, opaque);
        if (ret < 0 || opaque->inputThreadExit == false) {
            goto the_end;
        }

        if (!ret) {
            continue;
        }

        if (ffp->get_frame_mode) {
            if (!ffp->get_img_info || ffp->get_img_info->count <= 0) {
                av_frame_unref(frame);
                continue;
            }

            lastPts = dstPts;

            if (dstPts < 0) {
                dstPts = ffp->get_img_info->start_time;
            } else {
                dstPts += (ffp->get_img_info->end_time - ffp->get_img_info->start_time) / (ffp->get_img_info->num - 1);
            }

            pts = (frame->pts == AV_NOPTS_VALUE) ? NAN : frame->pts * av_q2d(tb);
            pts = pts * interval;
            if (pts >= dstPts) {
                while (retryConvertImage <= MAX_RETRY_CONVERT_IMAGE) {
                    ret = convert_image(ffp, frame, (int64_t)pts, frame->width, frame->height);
                    if (!ret) {
                        convertFrameCount++;
                        break;
                    }
                    retryConvertImage++;
                    av_log(NULL, AV_LOG_ERROR, "convert image error retryConvertImage = %d\n", retryConvertImage);
                }

                retryConvertImage = 0;
                if (ret || ffp->get_img_info->count <= 0) {
                    if (ret) {
                        av_log(NULL, AV_LOG_ERROR, "convert image abort ret = %d\n", ret);
                        ffp_notify_msg3(ffp, FFP_MSG_GET_IMG_STATE, 0, ret);
                    } else {
                        LOGE("convert image complete convertFrameCount = %d\n", convertFrameCount);
                    }
                    goto the_end;
                }
            } else {
                dstPts = lastPts;
            }
            av_frame_unref(frame);
            continue;
        }

        duration = (frameRate.num && frameRate.den ? av_q2d((AVRational){frameRate.den, frameRate.num}) : 0);
        pts = (frame->pts == AV_NOPTS_VALUE) ? NAN : frame->pts * av_q2d(tb);
        ret = ffp_queue_picture(ffp, frame, pts, duration, frame->pkt_pos, is->viddec.pkt_serial);
        av_frame_unref(frame);
        if (ret < 0) {
            goto the_end;
        }
    }
 the_end:
    opaque->inputThreadExit = false;
    pushInputThread.join();
    av_log(NULL, AV_LOG_INFO, "convert image convertFrameCount = %d\n", convertFrameCount);
    av_bsf_free(&opaque->avbsfContext);
    av_frame_free(&frame);
    return 0;
}


static int func_run_sync(IJKFF_Pipenode *node)
{
    IJKFF_Pipenode_Opaque *opaque = static_cast<IJKFF_Pipenode_Opaque *>(node->opaque);
    return ffplay_video_ohos_thread(opaque->ffp, opaque);
}

static int GetAvbsfContest(std::string bsfName, IJKFF_Pipenode_Opaque *decoderSample, AVCodecParameters *codecpar)
{
    void *i = nullptr;
    const AVBitStreamFilter *aVBitStreamFilter = {nullptr};
    while ((decoderSample->aVBitStreamFilter = av_bsf_iterate(&i))) {
        if (!strcmp(decoderSample->aVBitStreamFilter->name, bsfName.c_str())) {
            break;
        }
    }
    if (decoderSample->aVBitStreamFilter == nullptr) {
        return -1;
    }

    if (av_bsf_alloc(decoderSample->aVBitStreamFilter, &decoderSample->avbsfContext) < 0) {
        return -1;
    }

    if (avcodec_parameters_copy(decoderSample->avbsfContext->par_in, codecpar) < 0) {
        return -1;
    }

    if (av_bsf_init(decoderSample->avbsfContext) < 0) {
        return -1;
    }
    return 0;
}

IJKFF_Pipenode *ffpipenode_create_video_decoder_from_ohos_mediacodec(FFPlayer *ffp, IJKFF_Pipeline *pipeline,
    SDL_Vout *vout)
{
    std::string bsfName;
    AVStream *st = ffp->is->video_st;
    IJKFF_Pipenode *node = ffpipenode_alloc(sizeof(IJKFF_Pipenode_Opaque));
    IJKFF_Pipenode_Opaque *decoderSample = new IJKFF_Pipenode_Opaque();
    node->opaque = decoderSample;
    decoderSample->ffp = ffp;
    decoderSample->pipeline = pipeline;
    decoderSample->weakVout = vout;
    decoderSample->codecpar = avcodec_parameters_alloc();
    decoderSample->codecWrapper = new OhosVideoCodecWrapper();
    if (!decoderSample->codecpar) {
        return nullptr;
    }

    if (avcodec_parameters_from_context(decoderSample->codecpar, ffp->is->viddec.avctx) < 0) {
        return nullptr;
    }

    decoderSample->formatInfoEntry.fps = av_q2d(av_guess_frame_rate(ffp->is->ic, ffp->is->video_st, NULL));
    decoderSample->formatInfoEntry.videoHeight = decoderSample->codecpar->height;
    decoderSample->formatInfoEntry.videoWidth = decoderSample->codecpar->width;
    decoderSample->codecData.formatInfo = &decoderSample->formatInfoEntry;

    switch (decoderSample->codecpar->codec_id) {
        case AV_CODEC_ID_H264:
            bsfName = "h264_mp4toannexb";
            decoderSample->decoder.Create(OH_AVCODEC_MIMETYPE_VIDEO_AVC);
            break;
        case AV_CODEC_ID_HEVC:
            bsfName = "hevc_mp4toannexb";
            decoderSample->decoder.Create(OH_AVCODEC_MIMETYPE_VIDEO_HEVC);
            break;
        default:
            LOGE("codec_id failed = %d\n", decoderSample->codecpar->codec_id);
            break;
    }

    if (GetAvbsfContest(bsfName, decoderSample, ffp->is->video_st->codecpar) < 0) {
        LOGE("GetAvbsfContest failed");
        delete decoderSample->aVBitStreamFilter;
        av_bsf_free(&decoderSample->avbsfContext);
        return nullptr;
    }

    decoderSample->decoder.Config(&decoderSample->codecData);
    decoderSample->decoder.Start();
    decoderSample->codecData.Start();

    if (ffp->get_img_info != nullptr) {
        GetImgInfo *get_img_info = ffp->get_img_info;
        int fmt = get_img_info->frame_img_codec_ctx->pix_fmt;
    }

    node->func_destroy = func_destroy;
    node->func_run_sync = func_run_sync;
    return node;
}