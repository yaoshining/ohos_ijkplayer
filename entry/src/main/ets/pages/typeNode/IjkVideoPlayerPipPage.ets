/*
 * Copyright (C) 2025 Huawei Device Co., Ltd.
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
import { IjkplayerMapManager } from '../IjkplayerMapManager';
import { PipManager } from './PipManager';
import { XComponentLoadCallBack } from './XComponentLoadCallBack';
import router from '@ohos.router';
import { Callback } from '@ohos.base';
import {
  DeviceChangeReason,
  IjkMediaPlayer,
  InterruptEvent,
  InterruptHintType,
  LogUtils,
  OnBufferingUpdateListener,
  OnCompletionListener,
  OnErrorListener,
  OnInfoListener,
  OnPreparedListener,
  OnSeekCompleteListener,
  OnTimedTextListener,
  OnVideoSizeChangedListener
} from '@ohos/ijkplayer';
import prompt from '@ohos.promptAction';
import { PlayStatus } from '../../common/PlayStatus';
import { RouterParam } from '../RouterParam';
import abilityAccessCtrl from '@ohos.abilityAccessCtrl';
import photoAccessHelper from '@ohos.file.photoAccessHelper';
import fs from '@ohos.file.fs';
import { PiPWindow } from '@kit.ArkUI';
import { PipOnActionEventCallBack } from './PipOnActionEventCallBack';

@Entry
@Component
export struct IjkVideoPlayerPipPage {
  private xcomponentId: string = ""
  @State progressValue: number = 0;
  @State currentTime: string = "00:00";
  @State totalTime: string = "00:00";
  @State loadingVisible: Visibility = Visibility.None;
  @State replayVisible: Visibility = Visibility.None;
  @State slideEnable: boolean = true;
  @State aspRatio: number = 0.5;
  @State mContext: object | undefined = undefined;
  @State mFirst: boolean = true;
  @State mDestroyPage: boolean = false;
  @State playSpeed: string = '1f';
  @State volume: number = 1.0;
  @State oldSeconds: number = 0;
  @State isSeekTo: boolean = false;
  @State isCurrentTime: boolean = false;
  @State videoWidth: string = '100%';
  @State initAspectRatio: number = 1;
  @State videoAspectRatio: number = this.initAspectRatio;
  private videoUrl: string = '';
  private last: number = 0;
  @State videoParentAspectRatio: number = this.initAspectRatio;
  private CONTROL_PlayStatus: PlayStatus | undefined = PlayStatus.INIT;
  @State PROGRESS_MAX_VALUE: number = 100;
  @State updateProgressTimer: number = 0;
  @State curIndex: number = 0;
  @State recordProgressVisible: Visibility = Visibility.None;
  @State screenshotProgressVisible: Visibility = Visibility.None;
  @State recordSaveFilePath: string = getContext(this).cacheDir + "/record.mp4";
  private videoUrls: string[] =
    ["https://1251542705.vod2.myqcloud.com/4a8d9c67vodtransgzp1251542705/203109c63270835013529449619/v.f1419907.mp4",
      "https://getsamplefiles.com/download/mp4/sample-5.mp4",
    ];

  aboutToAppear() {
    if (PipManager.getInstance().isHasStartPip) {
      this.xcomponentId = PipManager.getInstance().xcomponentId;
      if (PipManager.getInstance().videoUrl) {
        this.videoUrl = PipManager.getInstance().videoUrl;
      }
      this.CONTROL_PlayStatus = PipManager.getInstance().playStatusMap.get(this.xcomponentId);
      if (this.xcomponentId) {
        IjkplayerMapManager.getInstance().playStatusMap.set(this.xcomponentId,
          (this.CONTROL_PlayStatus == PlayStatus.PLAY || this.CONTROL_PlayStatus == PlayStatus.PAUSE) ? true : false);
        IjkplayerMapManager.getInstance().destroyStatusMap.set(this.xcomponentId, false);
      }
      if (PipManager.getInstance().isPlayDone) {
        this.progressValue = this.PROGRESS_MAX_VALUE;
        this.showRePlay();
      }
      this.volume = PipManager.getInstance().volume;
    } else {
      this.xcomponentId = "xcomponentId_" + IjkplayerMapManager.generateId();
      PipManager.getInstance().xcomponentId = this.xcomponentId;
    }
    if (!this.videoUrl) {
      this.videoUrl = (router.getParams() as RouterParam).videoUrl;
    }
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
    PipManager.getInstance().ijkMediaPlayer.on('audioInterrupt', event);
    let deviceChangeEvent: Callback<InterruptEvent> = (event) => {
      LogUtils.getInstance().LOGI(`deviceChange event: ${JSON.stringify(event)}`);
      if (event.reason === DeviceChangeReason.REASON_NEW_DEVICE_AVAILABLE) {
        this.pause();
      } else if (event.reason === DeviceChangeReason.REASON_OLD_DEVICE_UNAVAILABLE) {
        this.pause();
      }
    }
    PipManager.getInstance().ijkMediaPlayer.on('deviceChange', deviceChangeEvent);

    if (PipManager.getInstance().isHasStartPip) {
      this.setMessageListener();
    }
    LogUtils.getInstance()
      .LOGI("aboutToAppear id " + this.xcomponentId + " isHasStartPip " + PipManager.getInstance().isHasStartPip +
        " PlayStatus " + this.CONTROL_PlayStatus);
  }

  aboutToDisappear() {
    LogUtils.getInstance()
      .LOGI("aboutToDisappear id " + this.xcomponentId + " isHasStartPip " + PipManager.getInstance().isHasStartPip);
    if (this.xcomponentId) {
      PipManager.getInstance().playStatusMap.set(this.xcomponentId, this.CONTROL_PlayStatus);
    }
    PipManager.getInstance().volume = this.volume;
    this.stopProgressTask();
    if (this.xcomponentId) {
      IjkplayerMapManager.getInstance().destroyStatusMap.set(this.xcomponentId, true);
    }
    this.mDestroyPage = true;
    PipManager.getInstance().ijkMediaPlayer.off('audioInterrupt');
    PipManager.getInstance().ijkMediaPlayer.off('deviceChange');
    if (PipManager.getInstance().isHasStartPip && (PipManager.getInstance().pipState !== PiPWindow.PiPState.STOPPED)) {
      return;
    }
    PipManager.getInstance().ijkMediaPlayer.setScreenOnWhilePlaying(false);
    this.stopRecord(false);
    if (this.CONTROL_PlayStatus !== PlayStatus.INIT) {
      this.stop();
    }
    PipManager.getInstance().setAutoStart(false);
    PipManager.getInstance().stopPip();
  }

  onPageShow() {
    LogUtils.getInstance()
      .LOGI("onPageShow id " + this.xcomponentId + " isHasStartPip " + PipManager.getInstance().isHasStartPip);
    if (this.mFirst && !PipManager.getInstance().isHasStartPip) {
      let _this = this;
      let callBack: XComponentLoadCallBack = {
        onLoadSuccess(context: object) {
          _this.initDelayPlay(context)
        }
      }
      PipManager.getInstance().createXComponentNode(this.getUIContext(), this.xcomponentId, callBack)
      PipManager.getInstance().addNode();
    }

    PipManager.getInstance().initPipController(getContext(this));
    if (PipManager.getInstance().isHasStartPip) {
      this.videoWidth = PipManager.getInstance().videoWidth;
      this.videoAspectRatio = PipManager.getInstance().videoAspectRatio;
      if (!PipManager.getInstance().isPlayDone) {
        this.startProgressTask();
      }
    }

    if (this.mContext && !this.mFirst) {
      PipManager.getInstance().addNode();
      this.startPlayOrResumePlay();
    }

  }

  onPageHide() {
    LogUtils.getInstance()
      .LOGI("onPageHide id " + this.xcomponentId + " isHasStartPip " + PipManager.getInstance().isHasStartPip);
    PipManager.getInstance().removeNode();
    if (!PipManager.getInstance().isHasStartPip) {
      this.pause();
    }
  }

  build() {
    Flex({ direction: FlexDirection.Column, alignItems: ItemAlign.Auto, justifyContent: FlexAlign.Start }) {
      Flex({ direction: FlexDirection.Column, alignItems: ItemAlign.Center, justifyContent: FlexAlign.Center }) {
        Text($r('app.string.ijk_player'))
          .fontSize('30px')
          .fontColor(Color.White)
          .margin('10px')
          .fontWeight(FontWeight.Bold)
      }.height('100px').width('100%').backgroundColor(Color.Black)

      Divider().vertical(false).strokeWidth('20px').color(Color.White).lineCap(LineCapStyle.Round)
      Stack({ alignContent: Alignment.Center }) {
        Column() {
          NodeContainer(PipManager.getInstance().getNodeController())
            .width(this.videoWidth)
            .aspectRatio(this.videoAspectRatio)
        }.aspectRatio(this.videoAspectRatio)

        Image($r('app.media.icon_replay'))
          .objectFit(ImageFit.Auto)
          .width('120px')
          .height('120px')
          .visibility(this.replayVisible)
          .border({ width: 0 })
          .borderStyle(BorderStyle.Dashed)
          .onClick(() => {
            this.startPlayOrResumePlay();
          })
        Image($r('app.media.icon_load'))
          .objectFit(ImageFit.Auto)
          .width('120px')
          .height('120px')
          .visibility(this.loadingVisible)
          .border({ width: 0 })
          .borderStyle(BorderStyle.Dashed)
      }.width('100%').backgroundColor('#000000').clip(true)

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
              let seekValue = value * (PipManager.getInstance().ijkMediaPlayer.getDuration() / 100);
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
        Button($r('app.string.Switch'))
          .onClick(() => {
            this.playNext();
          })
          .width('400px')
          .height('80px')
          .margin('15px')
      }

      Flex({ direction: FlexDirection.Row, alignItems: ItemAlign.Center, justifyContent: FlexAlign.Start }) {
        Button($r('app.string.1x'))
          .onClick(() => {
            if (!this.debounce()) {
              return;
            }
            this.playSpeed = '1f'
            PipManager.getInstance().ijkMediaPlayer.setSpeed("1f");
          })
          .width('400px')
          .height('80px')
          .margin('15px')

        Button($r('app.string.1_5x'))
          .onClick(() => {
            if (!this.debounce()) {
              return;
            }
            this.playSpeed = '1.5f'
            PipManager.getInstance().ijkMediaPlayer.setSpeed("1.5f");
          })
          .width('400px')
          .height('80px')
          .margin('15px')

        Button($r('app.string.2x'))
          .onClick(() => {
            this.playSpeed = '2f'
            PipManager.getInstance().ijkMediaPlayer.setSpeed("2f");
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
              PipManager.getInstance().ijkMediaPlayer.setVolume(this.volume.toString(), this.volume.toString());
            }
          })
      }

      Flex({ direction: FlexDirection.Row, alignItems: ItemAlign.Center, justifyContent: FlexAlign.Start }) {
        Button($r('app.string.startRecord'))
          .visibility(this.recordProgressVisible === Visibility.Visible ? Visibility.None : Visibility.Visible)
          .onClick(() => {
            this.startRecord()
          })
          .width('400px')
          .height('80px')
          .margin('15px')

        Progress({ value: 0, total: 100, type: ProgressType.Ring })
          .width(50).color(Color.Blue)
          .style({ strokeWidth: 10, status: ProgressStatus.LOADING }).visibility(this.recordProgressVisible)

        Button($r('app.string.stopRecord'))
          .visibility(this.recordProgressVisible === Visibility.Visible ? Visibility.None : Visibility.Visible)
          .onClick(() => {
            this.stopRecord(true)
          })
          .width('400px')
          .height('80px')
          .margin('15px')

        Progress({ value: 0, total: 100, type: ProgressType.Ring })
          .width(50).color(Color.Blue)
          .style({ strokeWidth: 10, status: ProgressStatus.LOADING }).visibility(this.screenshotProgressVisible)

        Button($r('app.string.screenshot'))
          .visibility(this.screenshotProgressVisible === Visibility.Visible ? Visibility.None : Visibility.Visible)
          .onClick(() => {
            this.screenshot()
          })
          .width('400px')
          .height('80px')
          .margin('15px')
      }

      Flex({ direction: FlexDirection.Row, alignItems: ItemAlign.Center, justifyContent: FlexAlign.Start }) {
        Button($r('app.string.startPip'))
          .onClick(() => {
            this.startPip();
          })
          .width('400px')
          .height('80px')
          .margin('15px')
      }
    }
  }

  private startPip() {
    let _this = this;
    let callBack: PipOnActionEventCallBack = {
      onActionEvent(control: PiPWindow.ControlEventParam) {
        if (control.controlType == PiPWindow.PiPControlType.VIDEO_PLAY_PAUSE) {
          if (control.status === PiPWindow.PiPControlStatus.PAUSE) {
            LogUtils.getInstance().LOGI("PIP status PAUSE");
            //暂停视频
            _this.pause();
          } else if (control.status === PiPWindow.PiPControlStatus.PLAY) {
            LogUtils.getInstance().LOGI("PIP status PLAY");
            if (PipManager.getInstance().xcomponentId) {
              IjkplayerMapManager.getInstance().destroyStatusMap.set(PipManager.getInstance().xcomponentId, false)
            }
            if(_this.CONTROL_PlayStatus === PlayStatus.PLAY) {
               _this.CONTROL_PlayStatus = PlayStatus.INIT;
            }
            //播放视频
            _this.startPlayOrResumePlay();
            if (PipManager.getInstance().xcomponentId) {
              PipManager.getInstance().playStatusMap.set(PipManager.getInstance().xcomponentId, PlayStatus.PLAY);
            }
          }
        }
      }
    }
    PipManager.getInstance().setAutoStart(true);
    PipManager.getInstance().startPip(callBack);
  }

  private initDelayPlay(context: object) {
    this.mContext = context;
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
      PipManager.getInstance().ijkMediaPlayer.start();
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
    let position = PipManager.getInstance().ijkMediaPlayer.getCurrentPosition();
    let duration = PipManager.getInstance().ijkMediaPlayer.getDuration();
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
      .LOGI("setProgress position:" + position + ",duration:" + duration + ",progressValue:" + this.progressValue);
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
    PipManager.getInstance().isPlayDone = true;
    this.loadingVisible = Visibility.None;
    this.replayVisible = Visibility.Visible;
  }

  private play(url: string) {
    if (IjkplayerMapManager.getInstance().destroyStatusMap.get(this.xcomponentId)) {
      return;
    }
    this.showLoadIng();
    PipManager.getInstance().isPlayDone = false;
    //设置XComponent回调的context
    if (!!this.mContext) {
      PipManager.getInstance().ijkMediaPlayer.setContext(this.mContext, this.xcomponentId);
    }
    if (this.CONTROL_PlayStatus === PlayStatus.INIT) {
      PipManager.getInstance().ijkMediaPlayer.reset();
    }
    this.CONTROL_PlayStatus = PlayStatus.PLAY;
    //设置debug模式
    PipManager.getInstance().ijkMediaPlayer.setDebug(true);
    //初始化配置
    PipManager.getInstance().ijkMediaPlayer.native_setup();
    // 初始化配置后需要重新设置音频流音量，否则音量为默认值1.0
    PipManager.getInstance().ijkMediaPlayer.setVolume(this.volume.toString(), this.volume.toString());
    //设置视频源
    PipManager.getInstance().ijkMediaPlayer.setDataSource(url);

    //使用精确寻帧 例如，拖动播放后，会寻找最近的关键帧进行播放，很有可能关键帧的位置不是拖动后的位置，而是较前的位置.可以设置这个参数来解决问题
    PipManager.getInstance().ijkMediaPlayer.setOption(IjkMediaPlayer.OPT_CATEGORY_PLAYER, "enable-accurate-seek", "1");
    //预读数据的缓冲区大小
    PipManager.getInstance().ijkMediaPlayer.setOption(IjkMediaPlayer.OPT_CATEGORY_PLAYER, "max-buffer-size", "102400");
    //停止预读的最小帧数
    PipManager.getInstance().ijkMediaPlayer.setOption(IjkMediaPlayer.OPT_CATEGORY_PLAYER, "min-frames", "100");
    //启动预加载
    PipManager.getInstance().ijkMediaPlayer.setOption(IjkMediaPlayer.OPT_CATEGORY_PLAYER, "start-on-prepared", "1");
    // 设置无缓冲，这是播放器的缓冲区，有数据就播放
    PipManager.getInstance().ijkMediaPlayer.setOption(IjkMediaPlayer.OPT_CATEGORY_PLAYER, "packet-buffering", "0");
    //跳帧处理,放CPU处理较慢时，进行跳帧处理，保证播放流程，画面和声音同步
    PipManager.getInstance().ijkMediaPlayer.setOption(IjkMediaPlayer.OPT_CATEGORY_PLAYER, "framedrop", "5");
    // 最大缓冲cache是3s， 有时候网络波动，会突然在短时间内收到好几秒的数据
    // 因此需要播放器丢包，才不会累积延时
    // 这个和第三个参数packet-buffering无关。
    PipManager.getInstance()
      .ijkMediaPlayer
      .setOption(IjkMediaPlayer.OPT_CATEGORY_PLAYER, "max_cached_duration", "3000");
    // 无限制收流
    PipManager.getInstance().ijkMediaPlayer.setOption(IjkMediaPlayer.OPT_CATEGORY_PLAYER, "infbuf", "1");
    PipManager.getInstance().ijkMediaPlayer.setOptionLong(IjkMediaPlayer.OPT_CATEGORY_PLAYER, "infbuf", "1")
    // 屏幕常亮
    PipManager.getInstance().ijkMediaPlayer.setScreenOnWhilePlaying(true);
    // 设置超时
    PipManager.getInstance().ijkMediaPlayer.setOption(IjkMediaPlayer.OPT_CATEGORY_FORMAT, "timeout", "10000000");
    PipManager.getInstance()
      .ijkMediaPlayer
      .setOption(IjkMediaPlayer.OPT_CATEGORY_FORMAT, "connect_timeout", "10000000");
    PipManager.getInstance()
      .ijkMediaPlayer
      .setOption(IjkMediaPlayer.OPT_CATEGORY_FORMAT, "addrinfo_timeout", "10000000");
    PipManager.getInstance()
      .ijkMediaPlayer
      .setOption(IjkMediaPlayer.OPT_CATEGORY_FORMAT, "dns_cache_timeout", "10000000");
    // 变速播放
    PipManager.getInstance().ijkMediaPlayer.setOption(IjkMediaPlayer.OPT_CATEGORY_PLAYER, "soundtouch", "1");
    PipManager.getInstance().ijkMediaPlayer.setSpeed(this.playSpeed);
    let Speed = PipManager.getInstance().ijkMediaPlayer.getSpeed()
    LogUtils.getInstance().LOGI('getSpeed--' + Speed)
    //是否开启循环播放
    PipManager.getInstance().ijkMediaPlayer.setLoopCount(false);

    this.setMessageListener();

    PipManager.getInstance().ijkMediaPlayer.prepareAsync();

    PipManager.getInstance().ijkMediaPlayer.start();
    if (this.xcomponentId) {
      IjkplayerMapManager.getInstance().playStatusMap.set(this.xcomponentId, true);
    }
  }

  private setMessageListener() {
    let mOnVideoSizeChangedListener: OnVideoSizeChangedListener = {
      onVideoSizeChanged: (width: number, height: number, sar_num: number, sar_den: number) => {
        if (height === 0) {
          return;
        }
        const va = width / height;
        const vpa = this.videoParentAspectRatio;
        if (vpa > va) {
          this.videoWidth = (width / (height * vpa)) * 100 + '%';
        } else {
          this.videoWidth = '100%';
        }
        if (width && height) {
          this.videoAspectRatio = width / height;
        }
        PipManager.getInstance().videoWidth = this.videoWidth;
        PipManager.getInstance().videoAspectRatio = this.videoAspectRatio;
        LogUtils.getInstance()
          .LOGI("setOnVideoSizeChangedListener-->go:" + width + "," + height + "," + sar_num + "," + sar_den +
            ", videoAspectRatio " + this.videoAspectRatio + " videoWidth " + this.videoWidth);
        this.getVideoSize();
        this.hideLoadIng();
      }
    }
    PipManager.getInstance().ijkMediaPlayer.setOnVideoSizeChangedListener(mOnVideoSizeChangedListener);
    let mOnPreparedListener: OnPreparedListener = {
      onPrepared: () => {
        LogUtils.getInstance().LOGI("setOnPreparedListener-->go");
      }
    }
    PipManager.getInstance().ijkMediaPlayer.setOnPreparedListener(mOnPreparedListener);

    let mOnTimedTextListener: OnTimedTextListener = {
      onTimedText: () => {
      }
    }
    PipManager.getInstance().ijkMediaPlayer.setOnTimedTextListener(mOnTimedTextListener)

    let mOnCompletionListener: OnCompletionListener = {
      onCompletion: () => {
        LogUtils.getInstance().LOGI("OnCompletionListener-->go")
        this.showRePlay();
        this.currentTime = this.stringForTime(PipManager.getInstance().ijkMediaPlayer.getDuration());
        this.progressValue = this.PROGRESS_MAX_VALUE;
        this.slideEnable = false;
        PipManager.getInstance().pipController?.updatePiPControlStatus(PiPWindow.PiPControlType.VIDEO_PLAY_PAUSE,
          PiPWindow.PiPControlStatus.PAUSE);
        this.stopRecord(false);
        this.stop();
      }
    }
    PipManager.getInstance().ijkMediaPlayer.setOnCompletionListener(mOnCompletionListener);

    let mOnBufferingUpdateListener: OnBufferingUpdateListener = {
      onBufferingUpdate: (percent: number) => {
        LogUtils.getInstance().LOGI("OnBufferingUpdateListener-->go:" + percent);
        let MediaInfo = PipManager.getInstance().ijkMediaPlayer.getMediaInfo()
        LogUtils.getInstance().LOGI('getMediaInfo---' + MediaInfo);
        let VideoWidth = PipManager.getInstance().ijkMediaPlayer.getVideoWidth()
        LogUtils.getInstance().LOGI('getVideoWidth---' + VideoWidth);

        let VideoHeight = PipManager.getInstance().ijkMediaPlayer.getVideoHeight()
        LogUtils.getInstance().LOGI('getVideoHeight---' + VideoHeight);

        let VideoSarNum = PipManager.getInstance().ijkMediaPlayer.getVideoSarNum()
        LogUtils.getInstance().LOGI('getVideoSarNum---' + VideoSarNum);

        let VideoSarDen = PipManager.getInstance().ijkMediaPlayer.getVideoSarDen()
        LogUtils.getInstance().LOGI('getVideoSarDen---' + VideoSarDen);

        let AudioSessionId = PipManager.getInstance().ijkMediaPlayer.getAudioSessionId()
        LogUtils.getInstance().LOGI('getAudioSessionId---' + AudioSessionId);

        let Looping = PipManager.getInstance().ijkMediaPlayer.isLooping()
        LogUtils.getInstance().LOGI('isLooping---' + Looping);
      }
    }
    PipManager.getInstance().ijkMediaPlayer.setOnBufferingUpdateListener(mOnBufferingUpdateListener);

    let mOnSeekCompleteListener: OnSeekCompleteListener = {
      onSeekComplete: () => {
        LogUtils.getInstance().LOGI("OnSeekCompleteListener-->go");
        this.startPlayOrResumePlay();
      }
    }
    PipManager.getInstance().ijkMediaPlayer.setOnSeekCompleteListener(mOnSeekCompleteListener);

    let mOnInfoListener: OnInfoListener = {
      onInfo: (what: number, extra: number) => {
        LogUtils.getInstance().LOGI("OnInfoListener-->go:" + what + "===" + extra);
        this.hideLoadIng();
      }
    }
    PipManager.getInstance().ijkMediaPlayer.setOnInfoListener(mOnInfoListener);


    let mOnErrorListener: OnErrorListener = {
      onError: (what: number, extra: number) => {
        this.stopProgressTask();
        LogUtils.getInstance().LOGI("OnErrorListener-->go:" + what + "===" + extra)
        this.hideLoadIng();
        prompt.showToast({
          message: getContext()
            .resourceManager
            .getStringByNameSync("Honey_the_video_is_playing_errant_The_system_is_wandering")
        });
      }
    }

    PipManager.getInstance().ijkMediaPlayer.setOnErrorListener(mOnErrorListener);
    PipManager.getInstance().ijkMediaPlayer.setMessageListener();
  }

  private getVideoSize() {
    let VideoWidth = PipManager.getInstance().ijkMediaPlayer.getVideoWidth();
    LogUtils.getInstance().LOGI("getVideoWidth---" + VideoWidth);

    let VideoHeight = PipManager.getInstance().ijkMediaPlayer.getVideoHeight();
    LogUtils.getInstance().LOGI("getVideoHeight---" + VideoHeight);
  }

  private pause() {
    if (PipManager.getInstance().ijkMediaPlayer.isPlaying()) {
      PipManager.getInstance().ijkMediaPlayer.pause();
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
    if (this.xcomponentId) {
      PipManager.getInstance().playStatusMap.set(this.xcomponentId, this.CONTROL_PlayStatus);
    }
    PipManager.getInstance().ijkMediaPlayer.stop();
    PipManager.getInstance().ijkMediaPlayer.release();
    this.stopProgressTask();
  }

  private seekTo(value: string) {
    PipManager.getInstance().ijkMediaPlayer.seekTo(value);

  }

  private playNext() {
    if (!this.debounce()) {
      return;
    }
    if (this.curIndex === this.videoUrls.length - 1) {
      this.curIndex = 0;
    } else {
      this.curIndex++;
    }
    this.CONTROL_PlayStatus = PlayStatus.INIT;
    this.stopRecord(false);
    this.stop();
    this.videoUrl = this.videoUrls[this.curIndex];
    PipManager.getInstance().videoUrl = this.videoUrl;
    this.startPlayOrResumePlay()
  }

  debounce() {
    const delay = 600;
    let cur = new Date().getTime();
    if (cur - this.last > delay) {
      this.last = cur;
      return true;
    }
    return false;
  }

  private startRecord() {
    let isRecord = PipManager.getInstance().ijkMediaPlayer.isRecord()
    if (isRecord) {
      prompt.showToast({
        message: $r('app.string.recordIng')
      });
      return
    }
    let result = PipManager.getInstance().ijkMediaPlayer.startRecord(this.recordSaveFilePath);
    prompt.showToast({
      message: result ? $r('app.string.start_record_success') : $r('app.string.start_record_failed')
    });
  }

  private stopRecord(isShowTip: boolean) {
    let isRecord = PipManager.getInstance().ijkMediaPlayer.isRecord()
    if (!isRecord) {
      if (isShowTip) {
        prompt.showToast({
          message: $r('app.string.record_not_enabled')
        });
      }
      return
    }
    this.recordProgressVisible = Visibility.Visible;
    PipManager.getInstance().ijkMediaPlayer.stopRecord().then((result) => {
      this.recordProgressVisible = Visibility.None;
      if (!result) {
        prompt.showToast({
          message: $r('app.string.stop_record_failed')
        });
        return;
      }
      let atManager = abilityAccessCtrl.createAtManager();
      atManager.requestPermissionsFromUser(getContext(this), ['ohos.permission.WRITE_IMAGEVIDEO']).then(async () => {
        let photoType: photoAccessHelper.PhotoType = photoAccessHelper.PhotoType.VIDEO;
        let extension: string = 'mp4';
        let options: photoAccessHelper.CreateOptions = {
          title: "record_" + new Date().getTime() + ""
        }
        let phAccessHelper = photoAccessHelper.getPhotoAccessHelper(getContext(this));
        phAccessHelper.createAsset(photoType, extension, options, (err, uri) => {
          LogUtils.getInstance().LOGI(`createAsset success uri:${uri}`)
          if (uri !== undefined) {
            let recordFile = fs.openSync(this.recordSaveFilePath);
            let albumFile = fs.openSync(uri, fs.OpenMode.READ_WRITE);
            fs.copyFileSync(recordFile.fd, albumFile.fd);
            fs.closeSync(recordFile);
            fs.closeSync(albumFile);
            prompt.showToast({
              message: $r('app.string.stop_record_success')
            });
          } else {
            prompt.showToast({
              message: $r('app.string.stop_record_failed')
            });
            LogUtils.getInstance().LOGI(`createAsset failed, error: ${err.code}, ${err.message}`)
          }
        });
      })
    })
  }

  private screenshot() {
    let saveFilePath = getContext(this).cacheDir + "/screen.jpg";
    this.screenshotProgressVisible = Visibility.Visible;
    PipManager.getInstance().ijkMediaPlayer.screenshot(saveFilePath).then((result) => {
      this.screenshotProgressVisible = Visibility.None;
      if (!result) {
        prompt.showToast({
          message: $r('app.string.screenshot_failed')
        });
        return;
      }
      let atManager = abilityAccessCtrl.createAtManager();
      atManager.requestPermissionsFromUser(getContext(this), ['ohos.permission.WRITE_IMAGEVIDEO']).then(async () => {
        let photoType: photoAccessHelper.PhotoType = photoAccessHelper.PhotoType.IMAGE;
        let extension: string = 'jpg';
        let options: photoAccessHelper.CreateOptions = {
          title: "screenshot_" + new Date().getTime() + ""
        }
        let phAccessHelper = photoAccessHelper.getPhotoAccessHelper(getContext(this));
        phAccessHelper.createAsset(photoType, extension, options, (err, uri) => {
          LogUtils.getInstance().LOGI(`createAsset success uri:${uri}`)
          if (uri !== undefined) {
            let screenshotFile = fs.openSync(saveFilePath);
            let albumFile = fs.openSync(uri, fs.OpenMode.READ_WRITE);
            fs.copyFileSync(screenshotFile.fd, albumFile.fd);
            fs.closeSync(screenshotFile);
            fs.closeSync(albumFile);
            prompt.showToast({
              message: $r('app.string.screenshot_success')
            });
          } else {
            prompt.showToast({
              message: $r('app.string.screenshot_failed')
            });
            LogUtils.getInstance().LOGI(`createAsset failed, error: ${err.code}, ${err.message}`)
          }
        });
      })
    });
  }
}