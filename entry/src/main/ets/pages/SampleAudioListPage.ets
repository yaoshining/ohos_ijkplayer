/*
 * Copyright (C) 2024 Huawei Device Co., Ltd.
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

import { Callback } from '@ohos.base';
import { IjkMediaPlayer, InterruptEvent, InterruptHintType, } from '@ohos/ijkplayer';
import { OnPreparedListener } from '@ohos/ijkplayer';
import { OnCompletionListener } from '@ohos/ijkplayer';
import { OnBufferingUpdateListener } from '@ohos/ijkplayer';
import { OnErrorListener, OnTimedTextListener } from '@ohos/ijkplayer';
import { OnInfoListener } from '@ohos/ijkplayer';
import { OnSeekCompleteListener } from '@ohos/ijkplayer';
import { LogUtils } from '@ohos/ijkplayer';
import { PlayStatus } from '../common/PlayStatus';
import prompt from '@ohos.promptAction';
import { IjkplayerMapManager } from './IjkplayerMapManager';

@Entry
@Component
struct SampleAudioListPage {
  @State progressValue: number = 0;
  @State currentTime: string = "00:00";
  @State totalTime: string = "00:00";
  @State loadingVisible: Visibility = Visibility.None;
  @State replayVisible: Visibility = Visibility.None;
  @State slideEnable: boolean = false;
  @State aspRatio: number = 0.5;
  @State mFirst: boolean = true;
  @State mDestroyPage: boolean = false;
  @State playSpeed: string = '1f';
  @State volume: number = 1.0;
  @State oldSeconds: number = 0;
  @State isSeekTo: boolean = false;
  @State isCurrentTime: boolean = false;
  private videoUrl: string = '';
  private  CONTROL_PlayStatus = PlayStatus.INIT;
  @State PROGRESS_MAX_VALUE: number = 100;
  private mIjkMediaPlayer = IjkMediaPlayer.getInstance();
  @State updateProgressTimer: number = 0;
  @State videoUrls: string[] = ["http://devimages.apple.com.edgekey.net/streaming/examples/bipbop_4x3/bipbop_4x3_variant.m3u8",
  "http://devimages.apple.com.edgekey.net/streaming/examples/bipbop_4x3/bipbop_4x3_variant.m3u8"
];
  @State curIndex: number = 0;
  private xcomponentId: string = ""

  aboutToAppear() {
    LogUtils.getInstance().LOGI("aboutToAppear");
    this.xcomponentId = "xcomponentId_" + IjkplayerMapManager.generateId();
    this.videoUrl = this.videoUrls[0]
    this.initDelayPlay();
    let event: Callback<InterruptEvent> = (event) => {
      LogUtils.getInstance().LOGI(`event: ${JSON.stringify(event)}`);
      if (event.hintType === InterruptHintType.INTERRUPT_HINT_PAUSE) {
        this.pause();
      } else if (event.hintType === InterruptHintType.INTERRUPT_HINT_RESUME) {
        this.startPlayOrResumePlay();
      } else if (event.hintType === InterruptHintType.INTERRUPT_HINT_STOP) {
        this.stop();
      }
    }
    this.mIjkMediaPlayer.on('audioInterrupt', event);
  }

  aboutToDisappear() {
    LogUtils.getInstance().LOGI("aboutToDisappear");
    IjkplayerMapManager.getInstance().destroyStatusMap.set(this.xcomponentId, true);
    this.mDestroyPage = true;
    this.mIjkMediaPlayer.setScreenOnWhilePlaying(false);
    if (this.CONTROL_PlayStatus !== PlayStatus.INIT) {
      this.stop();
    }
    this.mIjkMediaPlayer.off('audioInterrupt');
  }

  onPageShow() {
    if (!this.mFirst) {
      this.startPlayOrResumePlay();
    }
  }

  onPageHide() {
    this.pause();
  }

  build() {
    Flex({ direction: FlexDirection.Column, alignItems: ItemAlign.Auto, justifyContent: FlexAlign.Start }) {
      Flex({ direction: FlexDirection.Column, alignItems: ItemAlign.Center, justifyContent: FlexAlign.Center }) {
        Text($r('app.string.ijkplayer_Audio_player'))
          .fontSize('30px')
          .fontColor(Color.White)
          .margin('10px')
          .fontWeight(FontWeight.Bold)
      }.height('100px').width('100%').backgroundColor(Color.Black)

      Divider().vertical(false).strokeWidth('20px').color(Color.White).lineCap(LineCapStyle.Round)

      Flex({ direction: FlexDirection.Row, alignItems: ItemAlign.Center, justifyContent: FlexAlign.Start }) {
        Text(this.currentTime).width('100px').fontSize('20px').margin('20px')
        Slider({
          value: this.progressValue,
          min: 0,
          max: this.PROGRESS_MAX_VALUE,
          step: 1,
          style: SliderStyle.OutSet
        })
          .width('600px')
          .blockColor(Color.Blue)
          .trackColor(Color.Gray)
          .selectedColor(Color.Blue)
          .showSteps(true)
          .showTips(true)
          .enabled(this.slideEnable)
          .onChange((value: number, mode: SliderChangeMode) => {
            if (mode === 2) {
              this.isSeekTo = true;
              this.mDestroyPage = false;
              this.showLoadIng();
              LogUtils.getInstance().LOGI("slider-->seekValue start:" + value);
              let seekValue = value * (this.mIjkMediaPlayer.getDuration() / 100);
              this.seekTo(seekValue + "");
              this.setProgress()
              LogUtils.getInstance().LOGI("slider-->seekValue end:" + seekValue);
              this.isSeekTo = false;
            }
          })
        Text(this.totalTime).width('100px').fontSize('20px').margin('10px')
      }

      Flex({ direction: FlexDirection.Row, alignItems: ItemAlign.Center, justifyContent: FlexAlign.Start }) {
        Button($r('app.string.Play'))
          .onClick(() => {
            this.startPlayOrResumePlay();
          })
          .width('400px')
          .height('80px')
          .margin('15px')
        Button($r('app.string.Pause'))
          .onClick(() => {
            this.pause();
          })
          .width('400px')
          .height('80px')
          .margin('15px')
      }

      Flex({ direction: FlexDirection.Row, alignItems: ItemAlign.Center, justifyContent: FlexAlign.Start }) {
        Button($r('app.string.Stop'))
          .onClick(() => {
            this.stop();
          })
          .width('400px')
          .height('80px')
          .margin('15px')

        Button($r('app.string.Switch'))
          .onClick(() => {
            this.playNext();
          })
          .width('400px')
          .height('80px')
          .margin('15px')
      }

      Flex({ direction: FlexDirection.Row, alignItems: ItemAlign.Center, justifyContent: FlexAlign.Start }) {
        Button($r('app.string.1_5x'))
          .onClick(() => {
            this.playSpeed = '1.5f'
            this.stop();
            this.startPlayOrResumePlay()
          })
          .width('400px')
          .height('80px')
          .margin('15px')

        Button($r('app.string.2x'))
          .onClick(() => {
            this.playSpeed = '2f'
            this.stop();
            this.startPlayOrResumePlay()
          })
          .width('400px')
          .height('80px')
          .margin('15px')
      }
      Flex({ direction: FlexDirection.Row, alignItems: ItemAlign.Center, justifyContent: FlexAlign.Start }) {
        Text($r('app.string.Video_volume')).width('120px').fontSize('30px').margin('15px')
        Slider({
          value: this.volume,
          min: 0.0,
          max: 1.0,
          step: 0.1,
          style: SliderStyle.OutSet
        })
          .width('600px')
          .blockColor(Color.Blue)
          .trackColor(Color.Gray)
          .selectedColor(Color.Blue)
          .showSteps(true)
          .showTips(true)
          .onChange((value: number, mode: SliderChangeMode) => {
            if (mode === SliderChangeMode.End) {
              this.volume = value;
              this.mIjkMediaPlayer.setVolume(this.volume.toString(), this.volume.toString());
            }
          })
      }
    }
  }

  private initDelayPlay() {
    setTimeout(() => {
      this.startPlayOrResumePlay();
      this.mFirst = false;
    }, 300)
  }

  private startPlayOrResumePlay() {
    this.mDestroyPage = false;
    LogUtils.getInstance().LOGI("startPlayOrResumePlay start this.CONTROL_PlayStatus:" + this.CONTROL_PlayStatus)
    if (this.CONTROL_PlayStatus === PlayStatus.INIT) {
      this.stopProgressTask();
      this.startProgressTask();
      this.play(this.videoUrl.toString());
    }
    if (this.CONTROL_PlayStatus === PlayStatus.PAUSE) {
      this.mIjkMediaPlayer.start();
      this.setProgress()
    }
  }

  private completionNum(num: number): string | number {
    if (num < 10) {
      return '0' + num;
    } else {
      return num;
    }
  }

  private stringForTime(timeMs: number): string {
    let totalSeconds: number | string = (timeMs / 1000);
    let newSeconds: number | string = totalSeconds % 60;
    let minutes: number | string = (totalSeconds / 60) % 60;
    let hours: number | string = totalSeconds / 3600;
    LogUtils.getInstance().LOGI("stringForTime hours:" + hours + ",minutes:" + minutes + ",seconds:" + newSeconds);
    hours = this.completionNum(Math.floor(Math.floor(hours * 100) / 100));
    minutes = this.completionNum(Math.floor(Math.floor(minutes * 100) / 100));
    newSeconds = Math.floor(Math.floor(newSeconds * 100) / 100)
    if (this.isCurrentTime) {
      if (this.oldSeconds < newSeconds || newSeconds === 0 || this.isSeekTo) {
        this.oldSeconds = newSeconds
      } else {
        newSeconds = this.oldSeconds
      }
    }
    newSeconds = this.completionNum(newSeconds);
    if (hours > 0) {
      return hours + ":" + minutes + ":" + newSeconds;
    } else {
      return minutes + ":" + newSeconds;
    }
  }

  private setProgress() {
    if (IjkplayerMapManager.getInstance().destroyStatusMap.get(this.xcomponentId)) {
      return;
    }
    if (!IjkplayerMapManager.getInstance().playStatusMap.get(this.xcomponentId)) {
      return;
    }
    let position = this.mIjkMediaPlayer.getCurrentPosition();
    let duration = this.mIjkMediaPlayer.getDuration();
    let pos = 0;
    if (duration > 0) {
      this.slideEnable = true;
      let curPercent = position / duration;
      pos = curPercent * 100;
      if (pos > this.PROGRESS_MAX_VALUE) {
	    this.progressValue = this.PROGRESS_MAX_VALUE
	  } else {
	    this.progressValue = pos;
	  }
    }
    LogUtils.getInstance()
      .LOGI("setProgress position:" + position + ",duration:" + duration + ",progressValue:" + pos);
    this.totalTime = this.stringForTime(duration);
    if (position > duration) {
      position = duration;
    }
    this.isCurrentTime = true;
    this.currentTime = this.stringForTime(position);
    this.isCurrentTime = false
  }

  private startProgressTask() {
    this.updateProgressTimer = setInterval(() => {
      LogUtils.getInstance().LOGI("startProgressTask");
      if (IjkplayerMapManager.getInstance().destroyStatusMap.get(this.xcomponentId)) {
        clearInterval(this.updateProgressTimer);
        return;
      }
      if (!this.mDestroyPage) {
        this.setProgress();
      }
    }, 300);
  }

  private stopProgressTask() {
    LogUtils.getInstance().LOGI("stopProgressTask");
    clearInterval(this.updateProgressTimer);
  }

  private showLoadIng() {
    this.loadingVisible = Visibility.Visible;
    this.replayVisible = Visibility.None;
  }

  private hideLoadIng() {
    this.loadingVisible = Visibility.None;
    this.replayVisible = Visibility.None;
  }

  private showRePlay() {
    this.loadingVisible = Visibility.None;
    this.replayVisible = Visibility.Visible;
  }

  private play(url: string) {
    if (IjkplayerMapManager.getInstance().destroyStatusMap.get(this.xcomponentId)) {
      return;
    }
    this.showLoadIng();

    this.mIjkMediaPlayer.setAudioId(this.xcomponentId);
    if (this.CONTROL_PlayStatus === PlayStatus.INIT) {
      this.mIjkMediaPlayer.reset();
    }
    this.CONTROL_PlayStatus = PlayStatus.PLAY;
    //设置debug模式
    this.mIjkMediaPlayer.setDebug(true);
    //初始化配置
    this.mIjkMediaPlayer.native_setup();
    // 初始化配置后需要重新设置音频流音量，否则音量为默认值1.0
    this.mIjkMediaPlayer.setVolume(this.volume.toString(), this.volume.toString());
    //设置视频源
    this.mIjkMediaPlayer.setDataSource(url);
    //设置视频源http请求头
    let headers = new Map([
      ["user_agent", "Mozilla/5.0 BiliDroid/7.30.0 (bbcallen@gmail.com)"],
      ["referer", "https://www.bilibili.com"]
    ]);
    this.mIjkMediaPlayer.setDataSourceHeader(headers);
    //使用精确寻帧 例如，拖动播放后，会寻找最近的关键帧进行播放，很有可能关键帧的位置不是拖动后的位置，而是较前的位置.可以设置这个参数来解决问题
    this.mIjkMediaPlayer.setOption(IjkMediaPlayer.OPT_CATEGORY_PLAYER, "enable-accurate-seek", "1");
    //预读数据的缓冲区大小
    this.mIjkMediaPlayer.setOption(IjkMediaPlayer.OPT_CATEGORY_PLAYER, "max-buffer-size", "102400");
    //停止预读的最小帧数
    this.mIjkMediaPlayer.setOption(IjkMediaPlayer.OPT_CATEGORY_PLAYER, "min-frames", "100");
    //启动预加载
    this.mIjkMediaPlayer.setOption(IjkMediaPlayer.OPT_CATEGORY_PLAYER, "start-on-prepared", "1");
    // 设置无缓冲，这是播放器的缓冲区，有数据就播放
    this.mIjkMediaPlayer.setOption(IjkMediaPlayer.OPT_CATEGORY_PLAYER, "packet-buffering", "0");
    //跳帧处理,放CPU处理较慢时，进行跳帧处理，保证播放流程，画面和声音同步
    this.mIjkMediaPlayer.setOption(IjkMediaPlayer.OPT_CATEGORY_PLAYER, "framedrop", "5");
    // 最大缓冲cache是3s， 有时候网络波动，会突然在短时间内收到好几秒的数据
    // 因此需要播放器丢包，才不会累积延时
    // 这个和第三个参数packet-buffering无关。
    this.mIjkMediaPlayer.setOption(IjkMediaPlayer.OPT_CATEGORY_PLAYER, "max_cached_duration", "3000");
    // 无限制收流
    // this.mIjkMediaPlayer.setOption(IjkMediaPlayer.OPT_CATEGORY_PLAYER, "infbuf", "1");
    // this.mIjkMediaPlayer.setOptionLong(IjkMediaPlayer.OPT_CATEGORY_PLAYER, "infbuf", "1")
    // 屏幕常亮
    this.mIjkMediaPlayer.setScreenOnWhilePlaying(true);
    // 设置超时
    this.mIjkMediaPlayer.setOption(IjkMediaPlayer.OPT_CATEGORY_FORMAT, "timeout", "10000000");
    this.mIjkMediaPlayer.setOption(IjkMediaPlayer.OPT_CATEGORY_FORMAT, "connect_timeout", "10000000");
    this.mIjkMediaPlayer.setOption(IjkMediaPlayer.OPT_CATEGORY_FORMAT, "addrinfo_timeout", "10000000");
    this.mIjkMediaPlayer.setOption(IjkMediaPlayer.OPT_CATEGORY_FORMAT, "dns_cache_timeout", "10000000");
    // 变速播放
    this.mIjkMediaPlayer.setOption(IjkMediaPlayer.OPT_CATEGORY_PLAYER, "soundtouch", "1");
    this.mIjkMediaPlayer.setSpeed(this.playSpeed);
    let Speed = this.mIjkMediaPlayer.getSpeed()
    LogUtils.getInstance().LOGI('getSpeed--' + Speed)
    //是否开启循环播放
    this.mIjkMediaPlayer.setLoopCount(true);
    let mOnPreparedListener: OnPreparedListener = {
      onPrepared: () => {
        LogUtils.getInstance().LOGI("setOnPreparedListener-->go");
      }
    }
    this.mIjkMediaPlayer.setOnPreparedListener(mOnPreparedListener);

    let mOnTimedTextListener: OnTimedTextListener = {
      onTimedText: () => {
      }
    }
    this.mIjkMediaPlayer.setOnTimedTextListener(mOnTimedTextListener)

    let mOnCompletionListener: OnCompletionListener = {
      onCompletion: () => {
        LogUtils.getInstance().LOGI("OnCompletionListener-->go")
        this.showRePlay();
        this.currentTime = this.stringForTime(this.mIjkMediaPlayer.getDuration());
        this.progressValue = this.PROGRESS_MAX_VALUE;
        this.slideEnable = false;
        this.stop();
      }
    }
    this.mIjkMediaPlayer.setOnCompletionListener(mOnCompletionListener);

    let mOnBufferingUpdateListener: OnBufferingUpdateListener = {
      onBufferingUpdate: (percent: number) => {
        LogUtils.getInstance().LOGI("OnBufferingUpdateListener-->go:" + percent);
        let MediaInfo = this.mIjkMediaPlayer.getMediaInfo()
        LogUtils.getInstance().LOGI('getMediaInfo---' + MediaInfo);

        let Looping = this.mIjkMediaPlayer.isLooping()
        LogUtils.getInstance().LOGI('isLooping---' + Looping);
      }
    }
    this.mIjkMediaPlayer.setOnBufferingUpdateListener(mOnBufferingUpdateListener);

    let mOnSeekCompleteListener: OnSeekCompleteListener = {
      onSeekComplete: () => {
        LogUtils.getInstance().LOGI("OnSeekCompleteListener-->go");
        this.startPlayOrResumePlay();
      }
    }
    this.mIjkMediaPlayer.setOnSeekCompleteListener(mOnSeekCompleteListener);

    let mOnInfoListener: OnInfoListener = {
      onInfo: (what: number, extra: number) => {
        LogUtils.getInstance().LOGI("OnInfoListener-->go:" + what + "===" + extra);
        this.hideLoadIng();
      }
    }
    this.mIjkMediaPlayer.setOnInfoListener(mOnInfoListener);


    let mOnErrorListener: OnErrorListener = {
      onError: (what: number, extra: number) => {
        this.stopProgressTask();
        LogUtils.getInstance().LOGI("OnErrorListener-->go:" + what + "===" + extra)
        this.hideLoadIng();
        prompt.showToast({
          message: getContext().resourceManager.getStringByNameSync("Honey_the_video_is_playing_errant_The_system_is_wandering")
        });
      }
    }


    this.mIjkMediaPlayer.setOnErrorListener(mOnErrorListener);

    this.mIjkMediaPlayer.setMessageListener();

    this.mIjkMediaPlayer.prepareAsync();

    this.mIjkMediaPlayer.start();

    IjkplayerMapManager.getInstance().playStatusMap.set(this.xcomponentId, true);

  }

  private pause() {
    if (this.mIjkMediaPlayer.isPlaying()) {
      this.mIjkMediaPlayer.pause();
      this.setProgress();
      this.mDestroyPage = true;
      this.CONTROL_PlayStatus = PlayStatus.PAUSE;
    }
  }

  private stop() {
    if (!IjkplayerMapManager.getInstance().playStatusMap.get(this.xcomponentId)) {
      return;
    }
    this.CONTROL_PlayStatus = PlayStatus.INIT;
    this.mIjkMediaPlayer.stop();
    this.mIjkMediaPlayer.release();
    this.stopProgressTask();
  }

  private seekTo(value: string) {
    this.mIjkMediaPlayer.seekTo(value);

  }

  private playNext() {
    if (this.curIndex === this.videoUrls.length - 1) {
      this.curIndex = 0;
    } else {
      this.curIndex++;
    }
    this.CONTROL_PlayStatus = PlayStatus.INIT;
    this.stop();
    this.videoUrl = this.videoUrls[this.curIndex];
    this.startPlayOrResumePlay()
  }
}
