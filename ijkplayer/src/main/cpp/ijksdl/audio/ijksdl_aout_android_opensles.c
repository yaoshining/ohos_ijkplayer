/*****************************************************************************
 * ijksdl_aout_android_opensles.c
 *****************************************************************************
 *
 * Copyright (c) 2013 Bilibili
 * copyright (c) 2013 Zhang Rui <bbcallen@gmail.com>
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
 
#include "ijksdl_aout_android_opensles.h"
#include "ohaudio/native_audiorenderer.h"
#include "ohaudio/native_audiostreambuilder.h"
#include "ohaudio/native_audiostream_base.h"
#include "hilog/log.h"
#include "../ijksdl_class.h"
#include "../ijksdl_aout.h"
#include "../ijksdl_audio.h"
#include "../ijksdl_aout_internal.h"

static const int OPENSLES_BUFFERS = 255; /* maximum number of buffers */
static const int OPENSLES_BUFLEN = 10;   /* ms */
static const int GLOBAL_RESMGR = 0xFF00;
static const char *TAG = "[Sample_audio]";
static const int MS_TO_S = 1000;
static const int US_TO_S = 1000000;

SDL_Aout_Opaque *g_opaque = NULL;
static OH_AudioRenderer *audioRenderer = NULL;
static OH_AudioStreamBuilder *rendererBuilder = NULL;
static OH_AudioRenderer *audioRendererNormal = NULL; // 生成音频播放对象

static SDL_Class g_opensles_class = {
    .name = "OpenOhAudio",
};

typedef struct DataFormatPcm {
    Sint32 formatType;
    Sint32 numChannels;
    Sint32 samplesPerSec;
    Sint32 bitsPerSample;
    Sint32 containerSize;
    Sint32 channelMask;
    Sint32 endianness;
} OHDataFormatPcm;

typedef struct SDL_Aout_Opaque {
    FFPlayer *ffp;
    SDL_Thread * audio_tid;
    SDL_Thread _audio_tid;

    SDL_AudioSpec    spec;
    OHDataFormatPcm  formatPcm;
    int              bytes_per_frame;
    int              milli_per_buffer;
    int              frames_per_buffer;
    int              bytes_per_buffer;

    volatile bool  need_set_volume;
    volatile float left_volume;
    volatile float right_volume;

    volatile bool  abort_request;
    volatile bool  pause_on;
    volatile bool  need_flush;
    volatile bool  is_running;

    uint8_t       * buffer;
    size_t         buffer_capacity;
} SDL_Aout_Opaque;

static int32_t AudioRendererOnWriteData(OH_AudioRenderer *renderer, void *userData, void *buffer, int32_t bufferLen)
{
    SDL_Aout_Opaque *opaque = g_opaque;
    if ((opaque == NULL) || opaque->abort_request || opaque->pause_on) {
        return 0;
    }

    SDL_AudioCallback audioCallback = opaque->spec.callback;
    if (audioCallback != NULL) {
        audioCallback(opaque->spec.userdata, (uint8_t *)buffer, bufferLen);
    }
    return 0;
}

static int32_t AudioRendererOnInterrupt(OH_AudioRenderer *renderer, void *userData, OH_AudioInterrupt_ForceType type,
                                        OH_AudioInterrupt_Hint hint)
{
    LOGI("AudioRendererOnInterrupt type:%d, hint:%d", type, hint);
    if ((g_opaque == NULL) || (g_opaque->ffp == NULL)) {
        return -1;
    }
    ffp_notify_msg3(g_opaque->ffp, FFP_MSG_AUDIO_INTERRUPT, type, hint);
    return 0;
}

static double AoutGetLatencySeconds(SDL_Aout *aout)
{
    return 0;
}

// 音频渲染器初始化
static int AoutOpenAudio(SDL_Aout *aout, const SDL_AudioSpec *desired, SDL_AudioSpec *obtained)
{
    if (audioRendererNormal != NULL) {
        OH_AudioRenderer_Release(audioRendererNormal);
        OH_AudioStreamBuilder_Destroy(rendererBuilder);
        audioRendererNormal = NULL;
        rendererBuilder = NULL;
    }
    SDL_Aout_Opaque *opaque = aout->opaque;

    void *userdata = opaque->spec.userdata;
    OHDataFormatPcm *formatPcm = &opaque->formatPcm;
    opaque->spec = *desired;

    formatPcm->numChannels = desired->channels;
    formatPcm->samplesPerSec = desired->freq * MS_TO_S; // milli Hz 48000 * 1000
    formatPcm->bitsPerSample = AUDIO_U16LSB;
    formatPcm->containerSize = AUDIO_U16LSB;

    // create builder
    OH_AudioStreamBuilder_Create(&rendererBuilder, AUDIOSTREAM_TYPE_RENDERER);
    // set params and callbacks
    OH_AudioStreamBuilder_SetSamplingRate(rendererBuilder, desired->freq * MS_TO_S);
    OH_AudioStreamBuilder_SetChannelCount(rendererBuilder, desired->channels);
    OH_AudioStreamBuilder_SetSampleFormat(rendererBuilder, AUDIOSTREAM_SAMPLE_S16LE);
    OH_AudioStreamBuilder_SetEncodingType(rendererBuilder, AUDIOSTREAM_ENCODING_TYPE_RAW);
    // 当设备支持低时延通路时，开发者可以使用低时延模式创建播放器
    OH_AudioStreamBuilder_SetLatencyMode(rendererBuilder, AUDIOSTREAM_LATENCY_MODE_FAST);
    // 关键参数，仅OHAudio支持，根据音频用途设置，系统会根据此参数实现音频策略自适应
    OH_AudioStreamBuilder_SetRendererInfo(rendererBuilder, AUDIOSTREAM_USAGE_MOVIE);

    OH_AudioRenderer_Callbacks rendererCallbacks;

    opaque->bytes_per_frame = formatPcm->numChannels * formatPcm->bitsPerSample / AUDIO_U8;
    opaque->milli_per_buffer = OPENSLES_BUFLEN;
    opaque->frames_per_buffer =
        opaque->milli_per_buffer * formatPcm->samplesPerSec / US_TO_S; // samplesPerSec is in milli
    opaque->bytes_per_buffer = opaque->bytes_per_frame * opaque->frames_per_buffer;
    opaque->buffer_capacity = OPENSLES_BUFFERS * opaque->bytes_per_buffer;
    opaque->pause_on = true;
    opaque->abort_request = false;

    rendererCallbacks.OH_AudioRenderer_OnWriteData = AudioRendererOnWriteData; // 看下数据写入OnWriteData
    rendererCallbacks.OH_AudioRenderer_OnStreamEvent = NULL;                   // 自定义音频流事件函数
    rendererCallbacks.OH_AudioRenderer_OnInterruptEvent = AudioRendererOnInterrupt; // 自定义音频中断事件函数
    rendererCallbacks.OH_AudioRenderer_OnError = NULL; // 自定义异常回调函数

    // 设置输出音频流的回调，在生成音频播放对象时自动注册
    OH_AudioStreamBuilder_SetRendererCallback(rendererBuilder, rendererCallbacks, NULL);
    // 构造播放音频流
    OH_AudioStreamBuilder_GenerateRenderer(rendererBuilder, &audioRendererNormal);

    if (obtained != NULL) {
        *obtained = *desired;
        obtained->size = opaque->buffer_capacity;
        obtained->freq = formatPcm->samplesPerSec / MS_TO_S;
    }
    LOGI("audio->aout_open_audio end");
    return opaque->buffer_capacity;
}

static void AoutPauseAudio(SDL_Aout *aout, int pauseOn)
{
    if ((g_opaque == NULL) || (audioRendererNormal == NULL)) {
        return;
    }
    g_opaque->pause_on = pauseOn;
    // 非0表示暂停，0表示取消暂停继续播放
    if (pauseOn != 0) {
        OH_AudioRenderer_Pause(audioRendererNormal);
    } else {
        OH_AudioRenderer_Start(audioRendererNormal);
    }
    return;
}

static void AudioRendererStop(SDL_Aout *aout)
{
    if ((g_opaque == NULL) || (audioRendererNormal == NULL)) {
        return;
    }
    g_opaque->abort_request = true;
    OH_AudioRenderer_Stop(audioRendererNormal);
}

static void AudioRendererFlush(SDL_Aout *aout)
{
    if (audioRendererNormal == NULL) {
        return;
    }
    OH_AudioRenderer_Flush(audioRendererNormal); // 丢弃已经写入的音频数据
}

static void AudioRendererRelease(SDL_Aout *aout)
{
    AudioRendererStop(aout);
    if (audioRendererNormal != NULL) {
        OH_AudioStreamBuilder_Destroy(rendererBuilder);
        OH_AudioRenderer_Release(audioRendererNormal);
        audioRendererNormal = NULL;
    }
}

static void AoutSetVolume(SDL_Aout *aout, float leftVolume, float rightVolume)
{
    SDL_Aout_Opaque *opaque = aout->opaque;
    opaque->left_volume = leftVolume;
    opaque->right_volume = rightVolume;
    opaque->need_set_volume = true;
    LOGI("audio->aout_set_volume");
}

SDL_Aout *SDLAoutCreateForOpenSLES(FFPlayer *ffp) // 实现音频播放功能；
{
    LOGI("audio->SDL_AoutAndroid_CreateForOpenSLES");

    SDL_Aout *aout = SDL_Aout_CreateInternal(sizeof(SDL_Aout_Opaque));
    if (aout == NULL) {
        return NULL;
    }

    SDL_Aout_Opaque *opaque = aout->opaque;
    g_opaque = opaque;
    opaque->ffp = ffp;

    aout->free_l = AudioRendererRelease;
    aout->opaque_class = &g_opensles_class;
    aout->open_audio = AoutOpenAudio; // 打开音频

    aout->pause_audio = AoutPauseAudio; // 暂停或播放音频
    aout->flush_audio = AudioRendererFlush;
    aout->close_audio = AudioRendererStop; // 关闭音频
    aout->set_volume = AoutSetVolume;       // 设置音量
    aout->func_get_latency_seconds = AoutGetLatencySeconds;

    return aout;
}

bool SDL_AoutAndroid_IsObjectOfOpenSLES(SDL_Aout * aout)
{
    LOGI("audio->SDL_AoutAndroid_IsObjectOfOpenSLES");
    if (aout == NULL) {
        return false;
    }
    return aout->opaque_class == &g_opensles_class;
}