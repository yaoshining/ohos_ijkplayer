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

#include "Player.h"
#include <bits/alltypes.h>
#include "av_codec_sample_log.h"
#include "dfx/error/av_codec_sample_error.h"

#include <fcntl.h> // O_RDONLY
#include <sys/stat.h> // stat


#undef LOG_TAG
#define LOG_TAG "OH_player"

namespace {
using namespace std::chrono_literals;
constexpr int64_t MILLI_SECOND = 1000;
constexpr int64_t MICRO_SECOND = 1000000;
}

Player::~Player()
{
    Player::StartRelease();
}

int32_t Player::InitWithUri(const std::string &url)
{
    SampleInfo info;
    info.inputFilePath = url;
    return Init(info, false);
}

int32_t Player::InitWithLocalPath(const std::string &filePath)
{
    int fd = open(filePath.c_str(), O_RDONLY);
    struct stat fileStatus {};
    size_t fileSize = 0;
    if (stat(filePath.c_str(), &fileStatus) == 0) {
        fileSize = static_cast<size_t>(fileStatus.st_size);
    } else {
        AVCODEC_SAMPLE_LOGI("get stat failed");
        return AVCODEC_SAMPLE_ERR_ERROR;
    }

    SampleInfo info;
    info.inputFd = fd;
    info.inputFileOffset = 0;
    info.inputFileSize = fileSize;
    return Init(info, true);
}


int32_t Player::Init(SampleInfo &sampleInfo, bool fromLocal)
{
    std::lock_guard<std::mutex> lock(mutex_);
    CHECK_AND_RETURN_RET_LOG(!isStarted_, AVCODEC_SAMPLE_ERR_ERROR, "Already started.");
    CHECK_AND_RETURN_RET_LOG(demuxer_ == nullptr && videoDecoder_ == nullptr,
        AVCODEC_SAMPLE_ERR_ERROR, "Already started.");
    
    sampleInfo_ = sampleInfo;
    
    videoDecoder_ = std::make_unique<VideoDecoder>();
    demuxer_ = std::make_unique<Demuxer>();
    
    int32_t ret = demuxer_->Create(sampleInfo_, fromLocal);
    CHECK_AND_RETURN_RET_LOG(ret == AVCODEC_SAMPLE_ERR_OK, ret, "Create demuxer failed");
    ret = videoDecoder_->Create(sampleInfo_.codecMime);
    CHECK_AND_RETURN_RET_LOG(ret == AVCODEC_SAMPLE_ERR_OK, ret, "Create video decoder failed");

    decContext_ = new CodecUserData;
    sampleInfo_.window = reinterpret_cast<OHNativeWindow*>(nativeWindow_);

    ret = videoDecoder_->Config(sampleInfo_, decContext_);
    CHECK_AND_RETURN_RET_LOG(ret == AVCODEC_SAMPLE_ERR_OK, ret, "Decoder config failed");

    isReleased_ = false;
    AVCODEC_SAMPLE_LOGI("Succeed");
    return AVCODEC_SAMPLE_ERR_OK;
}

int32_t Player::Start()
{
    std::unique_lock<std::mutex> lock(mutex_);
    if (isStarted_ && isPaused_) {
        isPaused_ = false;
        doneCond_.notify_all();
        AVCODEC_SAMPLE_LOGI("Resumed");
        return AVCODEC_SAMPLE_ERR_OK;
    }

    CHECK_AND_RETURN_RET_LOG(!isStarted_, AVCODEC_SAMPLE_ERR_ERROR, "Already started.");
    CHECK_AND_RETURN_RET_LOG(decContext_ != nullptr,
        AVCODEC_SAMPLE_ERR_ERROR, "Already started.");
    CHECK_AND_RETURN_RET_LOG(demuxer_ != nullptr && videoDecoder_ != nullptr,
        AVCODEC_SAMPLE_ERR_ERROR, "Already started.");
    
    int32_t ret = videoDecoder_->Start();
    CHECK_AND_RETURN_RET_LOG(ret == AVCODEC_SAMPLE_ERR_OK, ret, "Decoder start failed");

    isStarted_ = true;
    decInputThread_ = std::make_unique<std::thread>(&Player::DecInputThread, this);
    decOutputThread_ = std::make_unique<std::thread>(&Player::DecOutputThread, this);
    if (decInputThread_ == nullptr || decOutputThread_ == nullptr) {
        AVCODEC_SAMPLE_LOGE("Create thread failed");
        StartRelease();
        return AVCODEC_SAMPLE_ERR_ERROR;
    }

    AVCODEC_SAMPLE_LOGI("Succeed");
    doneCond_.notify_all();
    return AVCODEC_SAMPLE_ERR_OK;
}

void Player::Stop()
{
    StartRelease();
}

void Player::Pause()
{
    std::unique_lock<std::mutex> lock(mutex_);
    isPaused_ = true;
    doneCond_.notify_all();
}

bool Player::IsPlaying() const
{
    return isStarted_ && !isPaused_;
}

int64_t Player::Duration() const
{
    // OH_MD_KEY_DURATION单位是微秒1:1000000，ijk的单位是毫秒1:1000
    int64_t duration = sampleInfo_.durationTime / MILLI_SECOND;
    AVCODEC_SAMPLE_LOGI("OHAVCODEC Player::Duration %{public}d", duration);
    return duration;
}

int64_t Player::Position() const
{
    int64_t position = sampleInfo_.frameInterval * decContext_->outputFrameCount_ / MILLI_SECOND;
    AVCODEC_SAMPLE_LOGI("OHAVCODEC Player::Position %{public}d", position);
    return position;
}

int32_t Player::SeekTo(int64_t millisecond)
{
    return demuxer_->SeekTo(millisecond);
}

void Player::SetSpeed(double speed)
{
    speed_ = speed;
    AVCODEC_SAMPLE_LOGI("OHAVCODEC Player::SetSpeed %{public}d", speed_);
}

double Player::GetSpeed() const
{
    AVCODEC_SAMPLE_LOGI("OHAVCODEC Player::GetSpeed %{public}d", speed_);
    return speed_;
}

void Player::StartRelease()
{
    if (!isReleased_) {
        isReleased_ = true;
        Release();
    }
}

void Player::Release()
{
    std::lock_guard<std::mutex> lock(mutex_);
    speed_ = 1.0f;
    isStarted_ = false;
    isPaused_ = false;
    if (decInputThread_ && decInputThread_->joinable()) {
        decInputThread_->detach();
        decInputThread_.reset();
    }
    if (decOutputThread_ && decOutputThread_->joinable()) {
        decOutputThread_->detach();
        decOutputThread_.reset();
    }
    if (demuxer_ != nullptr) {
        demuxer_->Release();
        demuxer_.reset();
    }
    if (videoDecoder_ != nullptr) {
        videoDecoder_->Release();
        videoDecoder_.reset();
    }
    if (decContext_ != nullptr) {
        delete decContext_;
        decContext_ = nullptr;
    }
    doneCond_.notify_all();
    // 触发回调
    if (sampleInfo_.playDoneCallback) {
        sampleInfo_.playDoneCallback(sampleInfo_.playDoneCallbackData);
    }
    close(sampleInfo_.inputFd);
    AVCODEC_SAMPLE_LOGI("Succeed");
}

void Player::DecInputThread()
{
    while (true) {
        // 停止
        CHECK_AND_BREAK_LOG(isStarted_, "Decoder input thread out");

        // 暂停
        std::unique_lock<std::mutex> pauseLock(mutex_);
        doneCond_.wait(pauseLock, [this]() { return !this->isPaused_;});
        pauseLock.unlock();

        std::unique_lock<std::mutex> lock(decContext_->inputMutex_);
        bool condRet = decContext_->inputCond_.wait_for(
            lock, 5s, [this]() { return !isStarted_ || !decContext_->inputBufferInfoQueue_.empty(); });
        CHECK_AND_BREAK_LOG(isStarted_, "Work done, thread out");
        CHECK_AND_CONTINUE_LOG(!decContext_->inputBufferInfoQueue_.empty(),
                               "Buffer queue is empty, continue, cond ret: %{public}d", condRet);

        CodecBufferInfo bufferInfo = decContext_->inputBufferInfoQueue_.front();
        decContext_->inputBufferInfoQueue_.pop();
        decContext_->inputFrameCount_++;
        lock.unlock();
        
        demuxer_->ReadSample(reinterpret_cast<OH_AVBuffer *>(bufferInfo.buffer), bufferInfo.attr);

        int32_t ret = videoDecoder_->PushInputData(bufferInfo);
        CHECK_AND_BREAK_LOG(ret == AVCODEC_SAMPLE_ERR_OK, "Push data failed, thread out");
        
        CHECK_AND_BREAK_LOG(!(bufferInfo.attr.flags & AVCODEC_BUFFER_FLAGS_EOS), "Catch EOS, thread out");
    }
    StartRelease();
}

void Player::DecOutputThread()
{
    sampleInfo_.frameInterval = MICRO_SECOND / (sampleInfo_.frameRate * speed_);
    while (true) {
        // 停止
        CHECK_AND_BREAK_LOG(isStarted_, "Decoder output thread out");

        // 暂停
        std::unique_lock<std::mutex> pauseLock(mutex_);
        doneCond_.wait(pauseLock, [this]() { return !this->isPaused_;});
        pauseLock.unlock();

        thread_local auto lastPushTime = std::chrono::system_clock::now();
        std::unique_lock<std::mutex> lock(decContext_->outputMutex_);
        bool condRet = decContext_->outputCond_.wait_for(
            lock, 5s, [this]() { return !isStarted_ || !decContext_->outputBufferInfoQueue_.empty(); });
        CHECK_AND_BREAK_LOG(isStarted_, "Decoder output thread out");
        CHECK_AND_CONTINUE_LOG(!decContext_->outputBufferInfoQueue_.empty(),
                               "Buffer queue is empty, continue, cond ret: %{public}d", condRet);

        CodecBufferInfo bufferInfo = decContext_->outputBufferInfoQueue_.front();
        decContext_->outputBufferInfoQueue_.pop();
        CHECK_AND_BREAK_LOG(!(bufferInfo.attr.flags & AVCODEC_BUFFER_FLAGS_EOS), "Catch EOS, thread out");
        decContext_->outputFrameCount_++;
        AVCODEC_SAMPLE_LOGW("Out buffer count: %{public}u, size: %{public}d, flag: %{public}u, pts: %{public}" PRId64,
                            decContext_->outputFrameCount_, bufferInfo.attr.size, bufferInfo.attr.flags,
                            bufferInfo.attr.pts);
        lock.unlock();

        int32_t ret = videoDecoder_->FreeOutputData(bufferInfo.bufferIndex, true);
        CHECK_AND_BREAK_LOG(ret == AVCODEC_SAMPLE_ERR_OK, "Decoder output thread out");
        
        std::this_thread::sleep_until(lastPushTime + std::chrono::microseconds(sampleInfo_.frameInterval));
        lastPushTime = std::chrono::system_clock::now();
    }
    AVCODEC_SAMPLE_LOGI("Exit, frame count: %{public}u", decContext_->outputFrameCount_);
    StartRelease();
}

void Player::NativeSetup(void *nativeWindow)
{
    nativeWindow_ = nativeWindow;
}