/*
 * Copyright (C) 2022 Huawei Device Co., Ltd.
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

#ifndef ijkplayer_ijkplayer_napi.h_H
#define ijkplayer_ijkplayer_napi .h_H
#include <string>
#include <unordered_map>
#include "../utils/napi/napi_utils.h"
#include <ace/xcomponent/native_interface_xcomponent.h>
#include <napi/native_api.h>
#include "uv.h"

class IJKPlayerNapi {

  public:
    ~IJKPlayerNapi() {}
    
    static IJKPlayerNapi *GetInstance() {
        return &IJKPlayerNapi ::ijkplayerNapi_;
    }

    static napi_value setDataSource(napi_env env, napi_callback_info info);
    static napi_value setOption(napi_env env, napi_callback_info info);
    static napi_value setOptionLong(napi_env env, napi_callback_info info);
    static napi_value setVolume(napi_env env, napi_callback_info info);
    static napi_value prepareAsync(napi_env env, napi_callback_info info);
    static napi_value start(napi_env env, napi_callback_info info);
    static napi_value stop(napi_env env, napi_callback_info info);
    static napi_value pause(napi_env env, napi_callback_info info);
    static napi_value reset(napi_env env, napi_callback_info info);
    static napi_value release(napi_env env, napi_callback_info info);
    static napi_value seekTo(napi_env env, napi_callback_info info);
    static napi_value isPlaying(napi_env env, napi_callback_info info);
    static napi_value getDuration(napi_env env, napi_callback_info info);
    static napi_value getCurrentPosition(napi_env env, napi_callback_info info);
    static napi_value setMessageListener(napi_env env, napi_callback_info info);
    static napi_value setPropertyFloat(napi_env env, napi_callback_info info);
    static napi_value getPropertyFloat(napi_env env, napi_callback_info info);
    static napi_value setPropertyLong(napi_env env, napi_callback_info info);
    static napi_value getPropertyLong(napi_env env, napi_callback_info info);
    static napi_value getAudioSessionId(napi_env env, napi_callback_info info);
    static napi_value setLoopCount(napi_env env, napi_callback_info info);
    static napi_value getLoopCount(napi_env env, napi_callback_info info);
    static napi_value getVideoCodecInfo(napi_env env, napi_callback_info info);
    static napi_value getAudioCodecInfo(napi_env env, napi_callback_info info);
    static napi_value setStreamSelected(napi_env env, napi_callback_info info);
    static napi_value getMediaMeta(napi_env env, napi_callback_info info);
    static napi_value nativeOpenlog(napi_env env, napi_callback_info info);
    bool Export(napi_env env, napi_value exports);
    static OH_NativeXComponent_Callback *GetNXComponentCallback();
    void SetNativeXComponent(OH_NativeXComponent *component);
    void OnSurfaceCreated(OH_NativeXComponent *component, void *window);
    void OnSurfaceChanged(OH_NativeXComponent *component, void *window);
    void OnSurfaceDestroyed(OH_NativeXComponent *component, void *window);
    void DispatchTouchEvent(OH_NativeXComponent *component, void *window);

  private:
    static IJKPlayerNapi ijkplayerNapi_;
    static OH_NativeXComponent_Callback callback_;
    OH_NativeXComponent *component_;
    std::string id_;
    uint64_t width_;
    uint64_t height_;
    double x_;
    double y_;
    OH_NativeXComponent_TouchEvent touchEvent_;
};
#endif //ijkplayer_ijkplayer_napi.h_H
