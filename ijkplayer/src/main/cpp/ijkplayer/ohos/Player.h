/*
 * Copyright (C) 2023 Huawei Device Co., Ltd.
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

#ifndef VIDEO_CODEC_PLAYER_H
#define VIDEO_CODEC_PLAYER_H

#include <bits/alltypes.h>
#include <mutex>
#include <memory>
#include <atomic>
#include <thread>
#include <unistd.h>
#include "video_decoder.h"
#include "demuxer.h"
#include "sample_info.h"

class Player {
public:
    Player() = default;
    ~Player();
    
    static Player& GetInstance()
    {
        static Player player;
        return player;
    }

    int32_t InitWithUri(const std::string &url);
    int32_t InitWithLocalPath(const std::string &filePath);
    int32_t Init(SampleInfo &sampleInfo, bool fromLocal);
    void NativeSetup(void *nativeWindow);
    int32_t Start();
    void Stop();
    void Pause();
    bool IsPlaying() const;
    void SetSpeed(double speed);
    double GetSpeed() const;

    // 总时长
    int64_t Duration() const;
    // 已播放时长
    int64_t Position() const;
    
    int32_t SeekTo(int64_t millisecond);

private:
    void DecInputThread();
    void DecOutputThread();
    void Release();
    void StartRelease();

    std::unique_ptr<VideoDecoder> videoDecoder_ = { nullptr };
    std::unique_ptr<Demuxer> demuxer_ = { nullptr };
    
    std::mutex mutex_;
    std::atomic<bool> isStarted_ { false };
    std::atomic<bool> isReleased_ { false };
    bool isPaused_ { false };
    std::unique_ptr<std::thread> decInputThread_ = { nullptr };
    std::unique_ptr<std::thread> decOutputThread_ = { nullptr };
    std::condition_variable doneCond_;
    SampleInfo sampleInfo_;
    CodecUserData *decContext_ = { nullptr };
    void* nativeWindow_ { nullptr };
    double speed_ { 1.0f };
};

#endif // VIDEO_CODEC_PLAYER_H