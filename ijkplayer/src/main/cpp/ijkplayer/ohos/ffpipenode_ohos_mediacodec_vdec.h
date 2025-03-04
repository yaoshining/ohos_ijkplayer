/*
 * ffpipenode_ohos_mediacodec_vdec.h
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

#ifndef FFPLAY__FF_FFPIPENODE_OHOS_MEDIACODEC_VDEC_H
#define FFPLAY__FF_FFPIPENODE_OHOS_MEDIACODEC_VDEC_H

extern "C" {
#include "ff_ffplay.h"
}

#include <thread>
#include "ff_ffplay_def.h"
#include "../../ijksdl/ijksdl_vout.h"

enum AVCodecSampleError : int {
    AVCODEC_SAMPLE_ERR_OK = 0,
    AVCODEC_SAMPLE_ERR_ERROR = -1,
};

typedef struct OhosVideoCodecWrapper {
    int width;
    int height;
    int stride;
    int slice_height;
    int color_format;
    int crop_top;
    int crop_bottom;
    int crop_left;
    int crop_right;
    int display_width;
    int display_height;
} OhosVideoCodecWrapper;

enum FormatType {
    FORMAT_TYPE_IMAGE_WIDTH,
    FORMAT_TYPE_IMAGE_HEIGHT,
    FORMAT_TYPE_VIDEO_STRIDE,
    FORMAT_TYPE_SLICE_HEIGHT,
    FORMAT_TYPE_PIXEL_FORMAT,
    FORMAT_TYPE_CROP_TOP,
    FORMAT_TYPE_CROP_BOTTOM,
    FORMAT_TYPE_CROP_LEFT,
    FORMAT_TYPE_CROP_RIGHT,
    FORMAT_TYPE_VIDEO_WIDTH,
    FORMAT_TYPE_VIDEO_HEIGHT,
    FORMAT_TYPE_NBR
};

extern "C" {
IJKFF_Pipenode *ffpipenode_create_video_decoder_from_ohos_mediacodec(FFPlayer *ffp, IJKFF_Pipeline *pipeline,
    SDL_Vout *vout);
}

#endif