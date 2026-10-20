/*
 * This file is part of mpv.
 *
 * mpv is free software; you can redistribute it and/or
 * modify it under the terms of the GNU Lesser General Public
 * License as published by the Free Software Foundation; either
 * version 2.1 of the License, or (at your option) any later version.
 *
 * mpv is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU Lesser General Public License for more details.
 *
 * You should have received a copy of the GNU Lesser General Public
 * License along with mpv.  If not, see <http://www.gnu.org/licenses/>.
 */

#include "ohos_common.h"
#include "common/msg.h"
#include "video/mp_image.h"
#include "vo.h"

struct vo_ohos_state {
    struct mp_log *log;
    OHNativeWindow *native_window;
    bool color_space_valid;
    OH_NativeBuffer_ColorSpace color_space;
    bool metadata_type_valid;
    OH_NativeBuffer_MetadataType metadata_type;
    bool static_metadata_valid;
    OH_NativeBuffer_StaticMetadata static_metadata;
    bool hdr_brightness_valid;
    float hdr_brightness;
};

static bool is_hdr(const struct pl_color_space *color)
{
    return color->transfer == PL_COLOR_TRC_PQ ||
           color->transfer == PL_COLOR_TRC_HLG;
}

static OH_NativeBuffer_ColorSpace get_color_space(
    const struct pl_color_space *color)
{
    if (color->transfer == PL_COLOR_TRC_PQ)
        return OH_COLORSPACE_DISPLAY_BT2020_PQ;
    if (color->transfer == PL_COLOR_TRC_HLG)
        return OH_COLORSPACE_DISPLAY_BT2020_HLG;
    return OH_COLORSPACE_DISPLAY_SRGB;
}

static OH_NativeBuffer_StaticMetadata get_static_metadata(
    const struct pl_color_space *color)
{
    struct pl_raw_primaries prim = color->hdr.prim;
    if (!pl_primaries_valid(&prim)) {
        const struct pl_raw_primaries *container =
            pl_raw_primaries_get(color->primaries);
        if (!container)
            container = pl_raw_primaries_get(PL_COLOR_PRIM_BT_2020);
        prim = *container;
    }

    return (OH_NativeBuffer_StaticMetadata){
        .smpte2086 = {
            .displayPrimaryRed = {prim.red.x, prim.red.y},
            .displayPrimaryGreen = {prim.green.x, prim.green.y},
            .displayPrimaryBlue = {prim.blue.x, prim.blue.y},
            .whitePoint = {prim.white.x, prim.white.y},
            .maxLuminance = color->hdr.max_luma,
            .minLuminance = color->hdr.min_luma,
        },
        .cta861 = {
            .maxContentLightLevel = color->hdr.max_cll,
            .maxFrameAverageLightLevel = color->hdr.max_fall,
        },
    };
}

static int64_t p27_monotonic_us(void)
{
    struct timespec ts;
    if (clock_gettime(CLOCK_MONOTONIC, &ts)) return -1;
    return (int64_t)ts.tv_sec * 1000000 + ts.tv_nsec / 1000;
}

static bool static_metadata_equal(const OH_NativeBuffer_StaticMetadata *a,
                                  const OH_NativeBuffer_StaticMetadata *b)
{
    // 只比较有效字段，不能读取结构体填充字节。
    return a->smpte2086.displayPrimaryRed.x == b->smpte2086.displayPrimaryRed.x &&
           a->smpte2086.displayPrimaryRed.y == b->smpte2086.displayPrimaryRed.y &&
           a->smpte2086.displayPrimaryGreen.x == b->smpte2086.displayPrimaryGreen.x &&
           a->smpte2086.displayPrimaryGreen.y == b->smpte2086.displayPrimaryGreen.y &&
           a->smpte2086.displayPrimaryBlue.x == b->smpte2086.displayPrimaryBlue.x &&
           a->smpte2086.displayPrimaryBlue.y == b->smpte2086.displayPrimaryBlue.y &&
           a->smpte2086.whitePoint.x == b->smpte2086.whitePoint.x &&
           a->smpte2086.whitePoint.y == b->smpte2086.whitePoint.y &&
           a->smpte2086.maxLuminance == b->smpte2086.maxLuminance &&
           a->smpte2086.minLuminance == b->smpte2086.minLuminance &&
           a->cta861.maxContentLightLevel == b->cta861.maxContentLightLevel &&
           a->cta861.maxFrameAverageLightLevel == b->cta861.maxFrameAverageLightLevel;
}

static void set_output_color(struct vo_ohos_state *ctx,
                             struct pl_color_space color)
{
    pl_color_space_infer(&color);

    bool hdr = is_hdr(&color);
    OH_NativeBuffer_ColorSpace color_space = get_color_space(&color);
    OH_NativeBuffer_MetadataType metadata_type = hdr
        ? (color.transfer == PL_COLOR_TRC_HLG ? OH_VIDEO_HDR_HLG
                                              : OH_VIDEO_HDR_HDR10)
        : OH_VIDEO_NONE;
    float hdr_brightness = hdr ? 1.0f : 0.0f;

    if (!ctx->color_space_valid || ctx->color_space != color_space) {
        int ret = OH_NativeWindow_SetColorSpace(ctx->native_window, color_space);
        if (ret == 0) {
            ctx->color_space = color_space;
            ctx->color_space_valid = true;
            MP_VERBOSE(ctx, "NativeWindow output switched to %s\n",
                       hdr ? (color.transfer == PL_COLOR_TRC_HLG
                                  ? "BT.2020 HLG" : "BT.2020 PQ")
                           : "sRGB");
        } else {
            MP_WARN(ctx, "Failed to set NativeWindow color space: %d\n", ret);
        }
    }

    bool metadata_type_changed = !ctx->metadata_type_valid ||
                                 ctx->metadata_type != metadata_type;
    if (metadata_type_changed) {
        int ret = OH_NativeWindow_SetMetadataValue(
            ctx->native_window, OH_HDR_METADATA_TYPE, sizeof(metadata_type),
            (uint8_t *)&metadata_type);
        if (ret == 0) {
            ctx->metadata_type = metadata_type;
            ctx->metadata_type_valid = true;
        } else {
            MP_WARN(ctx, "Failed to set NativeWindow HDR metadata type: %d\n",
                    ret);
        }
    }

    if (hdr) {
        OH_NativeBuffer_StaticMetadata metadata = get_static_metadata(&color);
        if (metadata_type_changed || !ctx->static_metadata_valid ||
            !static_metadata_equal(&ctx->static_metadata, &metadata)) {
            int ret = OH_NativeWindow_SetMetadataValue(
                ctx->native_window, OH_HDR_STATIC_METADATA, sizeof(metadata),
                (uint8_t *)&metadata);
            MP_INFO(ctx, "P27_META t=%"PRId64" window=%p type=%d peak=%.6f min=%.6f cll=%.6f fall=%.6f rc=%d\n",
                    p27_monotonic_us(), ctx->native_window, metadata_type,
                    metadata.smpte2086.maxLuminance, metadata.smpte2086.minLuminance,
                    metadata.cta861.maxContentLightLevel, metadata.cta861.maxFrameAverageLightLevel, ret);
            if (ret == 0) {
                ctx->static_metadata = metadata;
                ctx->static_metadata_valid = true;
            } else {
                // 类型切换或invalidate后的失败也必须重试，即使字段等于旧缓存。
                ctx->static_metadata_valid = false;
                MP_WARN(ctx, "Failed to set NativeWindow HDR static metadata: %d\n",
                        ret);
            }
        }
    } else {
        ctx->static_metadata_valid = false;
    }

    if (!ctx->hdr_brightness_valid || ctx->hdr_brightness != hdr_brightness) {
        int ret = OH_NativeWindow_NativeWindowHandleOpt(
            ctx->native_window, SET_HDR_WHITE_POINT_BRIGHTNESS, hdr_brightness);
        if (ret == 0) {
            ctx->hdr_brightness = hdr_brightness;
            ctx->hdr_brightness_valid = true;
        } else {
            MP_WARN(ctx, "Failed to set NativeWindow HDR brightness: %d\n", ret);
        }
    }
}

bool vo_ohos_init(struct vo *vo)
{
    vo->ohos = talloc_zero(vo, struct vo_ohos_state);
    struct vo_ohos_state *ctx = vo->ohos;

    *ctx = (struct vo_ohos_state){
        .log = mp_log_new(ctx, vo->log, "ohos"),
    };

    if (vo->opts->WinID == 0 || vo->opts->WinID == -1) {
        MP_FATAL(ctx, "Missing surface pointer\n");
        goto fail;
    }

    uint64_t surface = 0;
    memcpy(&surface, &vo->opts->WinID, sizeof(vo->opts->WinID));
    OH_NativeWindow_CreateNativeWindowFromSurfaceId(surface, &ctx->native_window);
    if (!ctx->native_window) {
        MP_FATAL(ctx, "Failed to create OHNativeWindow\n");
        goto fail;
    }

    return true;
fail:
    talloc_free(ctx);
    vo->ohos = NULL;
    return false;
}

void vo_ohos_uninit(struct vo *vo)
{
    struct vo_ohos_state *ctx = vo->ohos;
    if (!ctx)
        return;

    if (ctx->native_window)
        OH_NativeWindow_DestroyNativeWindow(ctx->native_window);

    talloc_free(ctx);
    vo->ohos = NULL;
}

OHNativeWindow *vo_ohos_native_window(struct vo *vo)
{
    struct vo_ohos_state *ctx = vo->ohos;
    return ctx->native_window;
}

bool vo_ohos_surface_size(struct vo *vo, int *out_w, int *out_h)
{
    struct vo_ohos_state *ctx = vo->ohos;

    int w = vo->opts->ohos_surface_size.w,
        h = vo->opts->ohos_surface_size.h;
    if (!w || !h)
        OH_NativeWindow_NativeWindowHandleOpt(ctx->native_window, GET_BUFFER_GEOMETRY, &h, &w);

    if (w <= 0 || h <= 0) {
        MP_ERR(ctx, "Failed to get height and width.\n");
        return false;
    }
    *out_w = w;
    *out_h = h;
    return true;
}

struct pl_color_space vo_ohos_preferred_csp(struct vo *vo)
{
    const struct pl_color_space color = vo_get_current_params(vo).color;

    if (color.transfer == PL_COLOR_TRC_PQ)
        return pl_color_space_hdr10;
    if (color.transfer == PL_COLOR_TRC_HLG)
        return pl_color_space_bt2020_hlg;
    return pl_color_space_srgb;
}

bool vo_ohos_set_color(struct vo *vo, struct mp_image_params *params)
{
    struct pl_color_space color = params ? params->color
                                         : pl_color_space_srgb;

    if (is_hdr(&color)) {
        color.primaries = PL_COLOR_PRIM_BT_2020;
        pl_color_space_infer(&color);
    } else {
        color = pl_color_space_srgb;
    }

    if (params)
        params->color = color;

    // 调用方的最终输出 hint 已包含当前帧及 tone-map/target 调整。
    // vo->params 仅随重配置更新，不能用它覆盖连续同 transfer 的元数据。
    set_output_color(vo->ohos, color);
    return true;
}

void vo_ohos_invalidate_color(struct vo *vo)
{
    struct vo_ohos_state *ctx = vo->ohos;

    ctx->color_space_valid = false;
    ctx->metadata_type_valid = false;
    ctx->static_metadata_valid = false;
    ctx->hdr_brightness_valid = false;
}
