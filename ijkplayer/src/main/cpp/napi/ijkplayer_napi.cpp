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

#include "ijkplayer_napi.h"

#ifdef __cplusplus
extern "C" {
#endif
#include "../proxy/ijkplayer_napi_proxy.h"

const int32_t STR_DEFAULT_SIZE = 1024;
const int32_t INDEX_0 = 0;
const int32_t INDEX_1 = 1;
const int32_t INDEX_2 = 2;
const int32_t INDEX_3 = 3;
const int32_t PARAM_COUNT_1 = 1;
const int32_t PARAM_COUNT_2 = 2;
const int32_t PARAM_COUNT_3 = 3;
const int32_t PARAM_COUNT_4 = 4;

IJKPlayerNapi IJKPlayerNapi::ijkplayerNapi_;
OH_NativeXComponent_Callback IJKPlayerNapi::callback_;

napi_env envMessage_;
napi_ref callBackRefMessage_;

struct CallbackContext {
    napi_env env = nullptr;
    napi_ref callbackRef = nullptr;
    int what = 0;
    int arg1 = 0;
    int arg2 = 0;
};

void messageCallBack(int what, int arg1, int arg2) {
    LOGI("napi-->messageCallBack");
    struct CallbackContext *context = new CallbackContext();
    context->env = envMessage_;
    uv_loop_s *loopMessage = nullptr;
    napi_get_uv_event_loop(context->env, &loopMessage);
    if (loopMessage == nullptr) {
        LOGI("napi-->loopMessage null");
        return;
    }
    uv_work_t *work = new (std::nothrow) uv_work_t;
    if (work == nullptr) {
        LOGI("napi-->work null");
        return;
    }
    context->what = what;
    context->arg1 = arg1;
    context->arg2 = arg2;
    context->callbackRef = callBackRefMessage_;
    work->data = (void *)context;
    uv_queue_work(
        loopMessage, work, [](uv_work_t *work) {},
        [](uv_work_t *work, int status) {
            LOGI("napi-->uv_queue_work");
            CallbackContext *context = (CallbackContext *)work->data;
            napi_value callback = nullptr;
            napi_get_reference_value(context->env, context->callbackRef, &callback);
            napi_value what_;
            napi_value arg1_;
            napi_value arg2_;
            napi_value obj_;
            napi_create_string_utf8(context->env, (char *)((std::to_string(context->what)).c_str()), NAPI_AUTO_LENGTH, &what_);
            napi_create_string_utf8(context->env, (char *)((std::to_string(context->arg1)).c_str()), NAPI_AUTO_LENGTH, &arg1_);
            napi_create_string_utf8(context->env, (char *)((std::to_string(context->arg2)).c_str()), NAPI_AUTO_LENGTH, &arg2_);
            napi_value argv[] = {what_, arg1_, arg2_};
            napi_value ret = 0;
            napi_call_function(context->env, nullptr, callback, 3, argv, &ret);
            if (work != nullptr) {
                delete work;
            }
            delete context;
            LOGI("napi-->uv_queue_work end");
        });
}

void post_event(void *weak_this, int what, int arg1, int arg2,char *obj) {
    LOGI("napi-->post_event-->what:%d", what);
    messageCallBack(what, arg1, arg2);
}

void setEnvMessage(const napi_env &env) {
    envMessage_ = env;
}

void setCallBackRefMessage(const napi_ref &callbackRef) {
    callBackRefMessage_ = callbackRef;
}

napi_value IJKPlayerNapi::setMessageListener(napi_env env, napi_callback_info info) {
    LOGI("napi-->msg----setMessageListener");
    size_t argc = 1;
    napi_value args[1];
    napi_get_cb_info(env, info, &argc, args, NULL, NULL);
    napi_value width;
    napi_value height;
    napi_value result = 0;
    napi_value callback = args[0];
    napi_ref callBackRefMessage_;
    napi_create_reference(env, callback, 1, &callBackRefMessage_);
    setCallBackRefMessage(callBackRefMessage_);
    setEnvMessage(env);
    message_loop_callback(post_event);
    return nullptr;
}

napi_value IJKPlayerNapi::setDataSource(napi_env env, napi_callback_info info) {
    LOGI("napi-->setDataSource");
    size_t argc = PARAM_COUNT_1;
    napi_value args[PARAM_COUNT_1] = {nullptr};
    napi_get_cb_info(env, info, &argc, args, nullptr, nullptr);
    std::string url;
    NapiUtil::JsValueToString(env, args[INDEX_0], STR_DEFAULT_SIZE, url);
    LOGI("napi-->setDataSource-->url:%s", (char *)url.c_str());
    IjkMediaPlayer_setDataSource((char *)url.c_str());
    return nullptr;
}

napi_value IJKPlayerNapi::setOption(napi_env env, napi_callback_info info) {
    LOGI("napi-->setOption");
    size_t argc = PARAM_COUNT_3;
    napi_value args[PARAM_COUNT_3] = {nullptr};
    napi_get_cb_info(env, info, &argc, args, nullptr, nullptr);
    std::string category;
    NapiUtil::JsValueToString(env, args[INDEX_0], STR_DEFAULT_SIZE, category);
    std::string key;
    NapiUtil::JsValueToString(env, args[INDEX_1], STR_DEFAULT_SIZE, key);
    std::string value;
    NapiUtil::JsValueToString(env, args[INDEX_2], STR_DEFAULT_SIZE, value);
    LOGI("napi-->setOption-->category:%d,key:%s,value:%s", NapiUtil::StringToInt(category), (char *)key.c_str(), (char *)value.c_str());
    IjkMediaPlayer_setOption(NapiUtil::StringToInt(category), (char *)key.c_str(), (char *)value.c_str());
    return nullptr;
}

napi_value IJKPlayerNapi::setOptionLong(napi_env env, napi_callback_info info) {
    LOGI("napi-->setOptionLong");
    size_t argc = PARAM_COUNT_3;
    napi_value args[PARAM_COUNT_3] = {nullptr};
    napi_get_cb_info(env, info, &argc, args, nullptr, nullptr);
    std::string category;
    NapiUtil::JsValueToString(env, args[INDEX_0], STR_DEFAULT_SIZE, category);
    std::string key;
    NapiUtil::JsValueToString(env, args[INDEX_1], STR_DEFAULT_SIZE, key);
    std::string value;
    NapiUtil::JsValueToString(env, args[INDEX_2], STR_DEFAULT_SIZE, value);
    LOGI("napi-->setOptionLong-->category:%d,key:%s,value:%s", NapiUtil::StringToInt(category), (char *)key.c_str(), (char *)value.c_str());
    IjkMediaPlayer_setOptionLong(NapiUtil::StringToInt(category), (char *)key.c_str(), NapiUtil::StringToInt(value));
    return nullptr;
}

napi_value IJKPlayerNapi::setVolume(napi_env env, napi_callback_info info) {
    LOGI("napi-->setVolume");
    size_t argc = PARAM_COUNT_2;
    napi_value args[PARAM_COUNT_2] = {nullptr};
    napi_get_cb_info(env, info, &argc, args, nullptr, nullptr);
    std::string leftVolume;
    NapiUtil::JsValueToString(env, args[INDEX_0], STR_DEFAULT_SIZE, leftVolume);
    std::string rightVolume;
    NapiUtil::JsValueToString(env, args[INDEX_1], STR_DEFAULT_SIZE, rightVolume);
    LOGI("napi-->setVolume-->leftVolume:%s,rightVolume:%s", (char *)leftVolume.c_str(), (char *)rightVolume.c_str());
    IjkMediaPlayer_setVolume(NapiUtil::StringToFloat(leftVolume), NapiUtil::StringToFloat(rightVolume));
    return nullptr;
}

napi_value IJKPlayerNapi::prepareAsync(napi_env env, napi_callback_info info) {
    LOGI("napi-->prepareAsync");
    IjkMediaPlayer_prepareAsync();
    return nullptr;
}

napi_value IJKPlayerNapi::start(napi_env env, napi_callback_info info) {
    LOGI("napi-->start");
    IjkMediaPlayer_start();
    return nullptr;
}

napi_value IJKPlayerNapi::stop(napi_env env, napi_callback_info info) {
    LOGI("napi-->stop");
    IjkMediaPlayer_stop();
    return nullptr;
}

napi_value IJKPlayerNapi::pause(napi_env env, napi_callback_info info) {
    LOGI("napi-->pause");
    IjkMediaPlayer_pause();
    return nullptr;
}

napi_value IJKPlayerNapi::reset(napi_env env, napi_callback_info info) {
    LOGI("napi-->reset");
    IjkMediaPlayer_reset();
    return nullptr;
}

napi_value IJKPlayerNapi::release(napi_env env, napi_callback_info info) {
    LOGI("napi-->release");
    IjkMediaPlayer_release();
    return nullptr;
}

napi_value IJKPlayerNapi::getDuration(napi_env env, napi_callback_info info) {
    LOGI("napi-->getDuration");
    int duration = IjkMediaPlayer_getDuration();
    return NapiUtil::SetNapiCallInt32(env, duration);
}

napi_value IJKPlayerNapi::getCurrentPosition(napi_env env, napi_callback_info info) {
    LOGI("napi-->getCurrentPosition");
    int currentPosition = IjkMediaPlayer_getCurrentPosition();
    return NapiUtil::SetNapiCallInt32(env, currentPosition);
}

napi_value IJKPlayerNapi::seekTo(napi_env env, napi_callback_info info) {
    LOGI("napi-->seekTo");
    size_t argc = PARAM_COUNT_1;
    napi_value args[PARAM_COUNT_1] = {nullptr};
    napi_get_cb_info(env, info, &argc, args, nullptr, nullptr);
    std::string msec;
    NapiUtil::JsValueToString(env, args[INDEX_0], STR_DEFAULT_SIZE, msec);
    LOGI("napi-->seekTo-->msec:%d", NapiUtil::StringToInt(msec));
    IjkMediaPlayer_seekTo(NapiUtil::StringToInt(msec));
    return nullptr;
}

napi_value IJKPlayerNapi::isPlaying(napi_env env, napi_callback_info info) {
    LOGI("napi-->isPlaying");
    return NapiUtil::SetNapiCallBool(env, IjkMediaPlayer_isPlaying());
}

napi_value IJKPlayerNapi::setPropertyFloat(napi_env env, napi_callback_info info) {
    LOGI("napi-->setPropertyFloat");
    size_t argc = PARAM_COUNT_2;
    napi_value args[PARAM_COUNT_2] = {nullptr};
    napi_get_cb_info(env, info, &argc, args, nullptr, nullptr);
    std::string id;
    NapiUtil::JsValueToString(env, args[INDEX_0], STR_DEFAULT_SIZE, id);
    std::string value;
    NapiUtil::JsValueToString(env, args[INDEX_1], STR_DEFAULT_SIZE, value);
    ijkMediaPlayer_setPropertyFloat(NapiUtil::StringToInt(id), NapiUtil::StringToFloat(value));
    return nullptr;
}

napi_value IJKPlayerNapi::getPropertyFloat(napi_env env, napi_callback_info info) {
    LOGI("napi-->getPropertyFloat");
    size_t argc = PARAM_COUNT_2;
    napi_value args[PARAM_COUNT_2] = {nullptr};
    napi_get_cb_info(env, info, &argc, args, nullptr, nullptr);
    std::string id;
    NapiUtil::JsValueToString(env, args[INDEX_0], STR_DEFAULT_SIZE, id);
    std::string value;
    NapiUtil::JsValueToString(env, args[INDEX_1], STR_DEFAULT_SIZE, value);
    float result = ijkMediaPlayer_getPropertyFloat(NapiUtil::StringToInt(id), NapiUtil::StringToFloat(value));
    napi_value napi_result;
    napi_create_string_utf8(env, (char *)((std::to_string(result)).c_str()), NAPI_AUTO_LENGTH, &napi_result);
    return napi_result;
}

napi_value IJKPlayerNapi::setPropertyLong(napi_env env, napi_callback_info info) {
    LOGI("napi-->setPropertyLong");
    size_t argc = PARAM_COUNT_2;
    napi_value args[PARAM_COUNT_2] = {nullptr};
    napi_get_cb_info(env, info, &argc, args, nullptr, nullptr);
    std::string id;
    NapiUtil::JsValueToString(env, args[INDEX_0], STR_DEFAULT_SIZE, id);
    std::string value;
    NapiUtil::JsValueToString(env, args[INDEX_1], STR_DEFAULT_SIZE, value);
    ijkMediaPlayer_setPropertyLong(NapiUtil::StringToInt(id), NapiUtil::StringToLong(value));
    return nullptr;
}

napi_value IJKPlayerNapi::getPropertyLong(napi_env env, napi_callback_info info) {
    LOGI("napi-->getPropertyLong");
    size_t argc = PARAM_COUNT_2;
    napi_value args[PARAM_COUNT_2] = {nullptr};
    napi_get_cb_info(env, info, &argc, args, nullptr, nullptr);
    std::string id;
    NapiUtil::JsValueToString(env, args[INDEX_0], STR_DEFAULT_SIZE, id);
    std::string value;
    NapiUtil::JsValueToString(env, args[INDEX_1], STR_DEFAULT_SIZE, value);
    long result = ijkMediaPlayer_getPropertyLong(NapiUtil::StringToInt(id), NapiUtil::StringToLong(value));
    napi_value napi_result;
    napi_create_string_utf8(env, (char *)((std::to_string(result)).c_str()), NAPI_AUTO_LENGTH, &napi_result);
    return napi_result;
}

napi_value IJKPlayerNapi::getAudioSessionId(napi_env env, napi_callback_info info) {
    LOGI("napi-->getAudioSessionId");
    int getAudioSessionId = IjkMediaPlayer_getAudioSessionId();
    return NapiUtil::SetNapiCallInt32(env, getAudioSessionId);
}

napi_value IJKPlayerNapi::setLoopCount(napi_env env, napi_callback_info info) {
    LOGI("napi-->setLoopCount");
    size_t argc = PARAM_COUNT_1;
    napi_value args[PARAM_COUNT_1] = {nullptr};
    napi_get_cb_info(env, info, &argc, args, nullptr, nullptr);
    std::string loop_count;
    NapiUtil::JsValueToString(env, args[INDEX_0], STR_DEFAULT_SIZE, loop_count);
    IjkMediaPlayer_setLoopCount(NapiUtil::StringToInt(loop_count));
    return nullptr;
}

napi_value IJKPlayerNapi::getLoopCount(napi_env env, napi_callback_info info) {
    LOGI("napi-->getLoopCount");
    int loop_count = IjkMediaPlayer_getLoopCount();
    return NapiUtil::SetNapiCallInt32(env, loop_count);
}

napi_value IJKPlayerNapi::getVideoCodecInfo(napi_env env, napi_callback_info info) {
    LOGI("napi-->getVideoCodecInfo");
    char *result = IjkMediaPlayer_getVideoCodecInfo();
    LOGI("napi-->getVideoCodecInfo result:%s", result);
    napi_value napi_result;
    napi_create_string_utf8(env, result, NAPI_AUTO_LENGTH, &napi_result);
    return napi_result;
}

napi_value IJKPlayerNapi::getAudioCodecInfo(napi_env env, napi_callback_info info) {
    LOGI("napi-->getAudioCodecInfo");
    char *result = IjkMediaPlayer_getAudioCodecInfo();
    napi_value napi_result;
    napi_create_string_utf8(env, result, NAPI_AUTO_LENGTH, &napi_result);
    return napi_result;
}

napi_value IJKPlayerNapi::setStreamSelected(napi_env env, napi_callback_info info) {
    LOGI("napi-->setStreamSelected");
    size_t argc = PARAM_COUNT_2;
    napi_value args[PARAM_COUNT_2] = {nullptr};
    napi_get_cb_info(env, info, &argc, args, nullptr, nullptr);
    std::string stream;
    NapiUtil::JsValueToString(env, args[INDEX_0], STR_DEFAULT_SIZE, stream);
    std::string select;
    NapiUtil::JsValueToString(env, args[INDEX_1], STR_DEFAULT_SIZE, select);
    ijkMediaPlayer_setStreamSelected(NapiUtil::StringToInt(stream), NapiUtil::StringToBool(select));
    return nullptr;
}

napi_value IJKPlayerNapi::getMediaMeta(napi_env env, napi_callback_info info) {
    LOGI("napi-->getMediaMeta");
    HashMap map = IjkMediaPlayer_getMediaMeta();
    HashMapIterator iterator = hashmap_iterator(map);
    std::string result = "";
    while (hashmap_hasNext(iterator)) {
        iterator = hashmap_next(iterator);
        LOGI("napi-->getMediaMeta { key: %s, value: %s, hashcode: %d }\n",
             (STRING)iterator->entry->key, (STRING)iterator->entry->value, iterator->hashCode);
        result.append("key:");
        result.append((STRING)iterator->entry->key);
        result.append(",");
        result.append("value:");
        result.append((STRING)iterator->entry->value);
        result.append(";");
    }
    hashmap_delete(map);
    napi_value napi_result;
    napi_create_string_utf8(env, (char *)(result.c_str()), NAPI_AUTO_LENGTH, &napi_result);
    return napi_result;
}

napi_value IJKPlayerNapi::nativeOpenlog(napi_env env, napi_callback_info info) {
    IjkMediaPlayer_native_openlog();
    LOGI("napi-->nativeOpenlog");
    return nullptr;
}

///////////////////////////////XComponent////////////////////////////////

void OnSurfaceCreatedCB(OH_NativeXComponent *component, void *window) {
    LOGI("napi-->OnSurfaceCreatedCB");
    int32_t ret;
    char idStr[OH_XCOMPONENT_ID_LEN_MAX + 1] = {};
    uint64_t idSize = OH_XCOMPONENT_ID_LEN_MAX + 1;
    ret = OH_NativeXComponent_GetXComponentId(component, idStr, &idSize);
    if (ret != OH_NATIVEXCOMPONENT_RESULT_SUCCESS) {
        return;
    }
    LOGI("napi-->OnSurfaceCreatedCB-->success");
    IjkMediaPlayer_native_setup(component, window);
}

void OnSurfaceChangedCB(OH_NativeXComponent *component, void *window) {
    LOGI("napi-->OnSurfaceChangedCB");
}

void OnSurfaceDestroyedCB(OH_NativeXComponent *component, void *window) {
    LOGI("napi-->OnSurfaceDestroyedCB");
}

void DispatchTouchEventCB(OH_NativeXComponent *component, void *window) {
    LOGI("napi-->DispatchTouchEventCB");
}

void IJKPlayerNapi::OnSurfaceCreated(OH_NativeXComponent *component, void *window) {
    LOGI("napi-->OnSurfaceCreated");
    int32_t ret = OH_NativeXComponent_GetXComponentSize(component, window, &width_, &height_);
    if (ret == OH_NATIVEXCOMPONENT_RESULT_SUCCESS) {
        LOGI("napi-->OnSurfaceCreated-->success");
    }
}

void IJKPlayerNapi::OnSurfaceChanged(OH_NativeXComponent *component, void *window) {
    LOGI("napi-->OnSurfaceChanged");
}

void IJKPlayerNapi::OnSurfaceDestroyed(OH_NativeXComponent *component, void *window) {
    LOGI("napi-->OnSurfaceDestroyed");
}

void IJKPlayerNapi::DispatchTouchEvent(OH_NativeXComponent *component, void *window) {
    LOGI("napi-->DispatchTouchEvent");
    int32_t ret = OH_NativeXComponent_GetTouchEvent(component, window, &touchEvent_);
    if (ret == OH_NATIVEXCOMPONENT_RESULT_SUCCESS) {
        LOGI("napi-->DispatchTouchEvent-->success");
    }
}

OH_NativeXComponent_Callback *IJKPlayerNapi::GetNXComponentCallback() {
    return &IJKPlayerNapi::callback_;
}

void IJKPlayerNapi::SetNativeXComponent(OH_NativeXComponent *component) {
    component_ = component;
    OH_NativeXComponent_RegisterCallback(component_, &IJKPlayerNapi::callback_);
}

void OnSurfaceListener() {
    auto renderCallback = IJKPlayerNapi::GetNXComponentCallback();
    renderCallback->OnSurfaceCreated = OnSurfaceCreatedCB;
    renderCallback->OnSurfaceChanged = OnSurfaceChangedCB;
    renderCallback->OnSurfaceDestroyed = OnSurfaceDestroyedCB;
    renderCallback->DispatchTouchEvent = DispatchTouchEventCB;
}

bool IJKPlayerNapi::Export(napi_env env, napi_value exports) {
    LOGI("napi-->Export");
    napi_status status;
    napi_value exportInstance = nullptr;
    OH_NativeXComponent *nativeXComponent = nullptr;
    int32_t ret;
    char idStr[OH_XCOMPONENT_ID_LEN_MAX + 1] = {};
    uint64_t idSize = OH_XCOMPONENT_ID_LEN_MAX + 1;
    status = napi_get_named_property(env, exports, OH_NATIVE_XCOMPONENT_OBJ, &exportInstance);
    if (status != napi_ok) {
        return false;
    }
    status = napi_unwrap(env, exportInstance, reinterpret_cast<void **>(&nativeXComponent));
    if (status != napi_ok) {
        return false;
    }
    ret = OH_NativeXComponent_GetXComponentId(nativeXComponent, idStr, &idSize);
    if (ret != OH_NATIVEXCOMPONENT_RESULT_SUCCESS) {
        return false;
    }
    SetNativeXComponent(nativeXComponent);
    OnSurfaceListener();
    LOGI("napi-->Export-->end");
    return true;
}

EXTERN_C_START
static napi_value Init(napi_env env, napi_value exports) {
    napi_property_descriptor desc[] = {
        DECLARE_NAPI_FUNCTION("_setDataSource", IJKPlayerNapi::setDataSource),
        DECLARE_NAPI_FUNCTION("_setOption", IJKPlayerNapi::setOption),
        DECLARE_NAPI_FUNCTION("_setOptionLong", IJKPlayerNapi::setOptionLong),
        DECLARE_NAPI_FUNCTION("_prepareAsync", IJKPlayerNapi::prepareAsync),
        DECLARE_NAPI_FUNCTION("_start", IJKPlayerNapi::start),
        DECLARE_NAPI_FUNCTION("_stop", IJKPlayerNapi::stop),
        DECLARE_NAPI_FUNCTION("_pause", IJKPlayerNapi::pause),
        DECLARE_NAPI_FUNCTION("_reset", IJKPlayerNapi::reset),
        DECLARE_NAPI_FUNCTION("_release", IJKPlayerNapi::release),
        DECLARE_NAPI_FUNCTION("_seekTo", IJKPlayerNapi::seekTo),
        DECLARE_NAPI_FUNCTION("_isPlaying", IJKPlayerNapi::isPlaying),
        DECLARE_NAPI_FUNCTION("_setMessageListener", IJKPlayerNapi::setMessageListener),
        DECLARE_NAPI_FUNCTION("_getDuration", IJKPlayerNapi::getDuration),
        DECLARE_NAPI_FUNCTION("_getCurrentPosition", IJKPlayerNapi::getCurrentPosition),
        DECLARE_NAPI_FUNCTION("_setPropertyFloat", IJKPlayerNapi::setPropertyFloat),
        DECLARE_NAPI_FUNCTION("_getPropertyFloat", IJKPlayerNapi::getPropertyFloat),
        DECLARE_NAPI_FUNCTION("_setPropertyLong", IJKPlayerNapi::setPropertyLong),
        DECLARE_NAPI_FUNCTION("_getPropertyLong", IJKPlayerNapi::getPropertyLong),
        DECLARE_NAPI_FUNCTION("_getAudioSessionId", IJKPlayerNapi::getAudioSessionId),
        DECLARE_NAPI_FUNCTION("_setVolume", IJKPlayerNapi::setVolume),
        DECLARE_NAPI_FUNCTION("_setLoopCount", IJKPlayerNapi::setLoopCount),
        DECLARE_NAPI_FUNCTION("_getLoopCount", IJKPlayerNapi::getLoopCount),
        DECLARE_NAPI_FUNCTION("_getVideoCodecInfo", IJKPlayerNapi::getVideoCodecInfo),
        DECLARE_NAPI_FUNCTION("_getAudioCodecInfo", IJKPlayerNapi::getAudioCodecInfo),
        DECLARE_NAPI_FUNCTION("_setStreamSelected", IJKPlayerNapi::setStreamSelected),
        DECLARE_NAPI_FUNCTION("_getMediaMeta", IJKPlayerNapi::getMediaMeta),
        DECLARE_NAPI_FUNCTION("_nativeOpenlog", IJKPlayerNapi::nativeOpenlog),
    };
    NAPI_CALL(env, napi_define_properties(env, exports, sizeof(desc) / sizeof(desc[0]), desc));
    IJKPlayerNapi::GetInstance()->Export(env, exports);
    return exports;
}
EXTERN_C_END

static napi_module ijkplayerModule = {
    .nm_version = 1,
    .nm_flags = 0,
    .nm_filename = nullptr,
    .nm_register_func = Init,
    .nm_modname = "ijkplayer_napi",
    .nm_priv = ((void *)0),
    .reserved = {0},
};

extern "C" __attribute__((constructor)) void RegisterModule(void) {
    napi_module_register(&ijkplayerModule);
}

#ifdef __cplusplus
}
#endif