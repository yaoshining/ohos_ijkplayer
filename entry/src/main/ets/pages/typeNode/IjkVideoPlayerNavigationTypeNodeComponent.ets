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
import abilityAccessCtrl from '@ohos.abilityAccessCtrl';
import photoAccessHelper from '@ohos.file.photoAccessHelper';
import fs from '@ohos.file.fs';
import { IjkplayerMapManager } from '../IjkplayerMapManager';
import { FrameNode, NodeController, typeNode } from '@kit.ArkUI';

class DynamicsNodeController extends NodeController {
  public rootNode: FrameNode | null = null;

  makeNode(uiContext: UIContext): FrameNode | null {
    if (!this.rootNode) {
      this.rootNode = new FrameNode(uiContext);
      this.rootNode.commonAttribute
        .width("100%")
        .backgroundColor(Color.Black)
    }
    return this.rootNode;
  }
}

@Builder
export function IjkVideoPlayerTypeNodeNavigationComponentBuilder(name: string, param: Object) {
  IjkVideoPlayerTypeNodeNavigationComponent({ videoUrl: param as string })
}

@Component
struct IjkVideoPlayerTypeNodeNavigationComponent {
  @State progressValue: number = 0;
  @State currentTime: string = "00:00";
  @State totalTime: string = "00:00";
  @State loadingVisible: Visibility = Visibility.None;
  @State replayVisible: Visibility = Visibility.None;
  @State slideEnable: boolean = false;
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
  private mIjkMediaPlayer = IjkMediaPlayer.getInstance();
  private CONTROL_PlayStatus = PlayStatus.INIT;
  @State PROGRESS_MAX_VALUE: number = 100;
  @State updateProgressTimer: number = 0;
  @State curIndex: number = 0;
  @State recordProgressVisible: Visibility = Visibility.None;
  @State screenshotProgressVisible: Visibility = Visibility.None;
  @State recordSaveFilePath: string = "";
  private xcomponentId: string = ""
  private videoUrls: string[] =
    ["https://1251542705.vod2.myqcloud.com/4a8d9c67vodtransgzp1251542705/203109c63270835013529449619/v.f1419907.mp4",
      "https://getsamplefiles.com/download/mp4/sample-5.mp4"
    ];
  controller: DynamicsNodeController = new DynamicsNodeController();

  createXComponentNode() {
    let controller: XComponentController = new XComponentController();
    let options: XComponentOptions = {
      type: XComponentType.SURFACE,
      controller: controller
    };
    let xcomponentNode = typeNode.createNode(this.getUIContext(), "XComponent", options);
    xcomponentNode.commonAttribute.id(this.xcomponentId);
    xcomponentNode.attribute.width('100%');
    xcomponentNode.initialize({
      id: this.xcomponentId,
      type: XComponentType.SURFACE,
      libraryname: 'ijkplayer_napi',
      controller: controller
    }).onLoad((context: object) => {
      this.initDelayPlay(context);
    });
    this.controller.rootNode?.appendChild(xcomponentNode)
  }

  init() {
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
    let deviceChangeEvent: Callback<InterruptEvent> = (event) => {
      LogUtils.getInstance().LOGI(`deviceChange event: ${JSON.stringify(event)}`);
      if (event.reason === DeviceChangeReason.REASON_NEW_DEVICE_AVAILABLE) {
        this.pause();
      } else if (event.reason === DeviceChangeReason.REASON_OLD_DEVICE_UNAVAILABLE) {
        this.pause();
      }
    }
    this.mIjkMediaPlayer.on('deviceChange', deviceChangeEvent);
  }

  destroy() {
    LogUtils.getInstance().LOGI("destroy:" + this.xcomponentId);
    if (this.xcomponentId) {
      IjkplayerMapManager.getInstance().destroyStatusMap.set(this.xcomponentId, true);
    }
    this.mDestroyPage = true;
    this.mIjkMediaPlayer.setScreenOnWhilePlaying(false);
    this.stopRecord(false);
    if (this.CONTROL_PlayStatus !== PlayStatus.INIT) {
      this.stop();
    }
    this.mIjkMediaPlayer.off('audioInterrupt');
    this.mIjkMediaPlayer.off('deviceChange');
  }

  build() {
    NavDestination() {
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
            NodeContainer(this.controller)
              .width('100%')
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
              this.mIjkMediaPlayer.setSpeed("1f");
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
              this.mIjkMediaPlayer.setSpeed("1.5f");
            })
            .width('400px')
            .height('80px')
            .margin('15px')

          Button($r('app.string.2x'))
            .onClick(() => {
              this.playSpeed = '2f'
              this.mIjkMediaPlayer.setSpeed("2f");
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

      }
    }.onWillAppear(() => {
      this.xcomponentId = "xcomponentId_" + IjkplayerMapManager.generateId();
      LogUtils.getInstance().setLogSwitch(true)
      LogUtils.getInstance().LOGI("IjkVideoPlayer onWillAppear " + this.xcomponentId);
      this.init()
    }).onWillDisappear(() => {
      LogUtils.getInstance().LOGI("IjkVideoPlayer onWillDisappear " + this.xcomponentId);
      this.destroy()
    }).onWillShow(() => {
      if (this.mFirst) {
        this.createXComponentNode();
      }
      if (this.mContext && !this.mFirst) {
        this.startPlayOrResumePlay();
      }
    }).onWillHide(() => {
      if (this.mContext && !this.mFirst) {
        this.startPlayOrResumePlay();
      }
    })
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
    let result = IjkplayerMapManager.getInstance().playStatusMap.get(this.xcomponentId);
    if (!result) {
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
    //设置XComponent回调的context
    if (!!this.mContext) {
      this.mIjkMediaPlayer.setContext(this.mContext, this.xcomponentId);
    }
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
    this.mIjkMediaPlayer.setLoopCount(false);
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
        LogUtils.getInstance()
          .LOGI("setOnVideoSizeChangedListener-->go:" + width + "," + height + "," + sar_num + "," + sar_den);
        this.getVideoSize();
        this.hideLoadIng();
      }
    }
    this.mIjkMediaPlayer.setOnVideoSizeChangedListener(mOnVideoSizeChangedListener);
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
        this.stopRecord(false);
        this.stop();
      }
    }
    this.mIjkMediaPlayer.setOnCompletionListener(mOnCompletionListener);

    let mOnBufferingUpdateListener: OnBufferingUpdateListener = {
      onBufferingUpdate: (percent: number) => {
        LogUtils.getInstance().LOGI("OnBufferingUpdateListener-->go:" + percent);
        let MediaInfo = this.mIjkMediaPlayer.getMediaInfo()
        LogUtils.getInstance().LOGI('getMediaInfo---' + MediaInfo);
        let VideoWidth = this.mIjkMediaPlayer.getVideoWidth()
        LogUtils.getInstance().LOGI('getVideoWidth---' + VideoWidth);

        let VideoHeight = this.mIjkMediaPlayer.getVideoHeight()
        LogUtils.getInstance().LOGI('getVideoHeight---' + VideoHeight);

        let VideoSarNum = this.mIjkMediaPlayer.getVideoSarNum()
        LogUtils.getInstance().LOGI('getVideoSarNum---' + VideoSarNum);

        let VideoSarDen = this.mIjkMediaPlayer.getVideoSarDen()
        LogUtils.getInstance().LOGI('getVideoSarDen---' + VideoSarDen);

        let AudioSessionId = this.mIjkMediaPlayer.getAudioSessionId()
        LogUtils.getInstance().LOGI('getAudioSessionId---' + AudioSessionId);

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
          message: getContext()
            .resourceManager
            .getStringByNameSync("Honey_the_video_is_playing_errant_The_system_is_wandering")
        });
      }
    }


    this.mIjkMediaPlayer.setOnErrorListener(mOnErrorListener);

    this.mIjkMediaPlayer.setMessageListener();

    this.mIjkMediaPlayer.prepareAsync();

    this.mIjkMediaPlayer.start();

    if(this.xcomponentId){
      IjkplayerMapManager.getInstance().playStatusMap.set(this.xcomponentId, true);
    }
  }

  private getVideoSize() {
    let VideoWidth = this.mIjkMediaPlayer.getVideoWidth();
    LogUtils.getInstance().LOGI("getVideoWidth---" + VideoWidth);

    let VideoHeight = this.mIjkMediaPlayer.getVideoHeight();
    LogUtils.getInstance().LOGI("getVideoHeight---" + VideoHeight);
  }

  private pause() {
    if (this.mIjkMediaPlayer.isPlaying()) {
      this.mIjkMediaPlayer.pause();
      this.setProgress();
      this.mDestroyPage = true;
      this.CONTROL_PlayStatus = PlayStatus.PAUSE;
    }
  }

  private stop(): Promise<void> {
    return new Promise(async (resolve, reject) => {
      let result = IjkplayerMapManager.getInstance().playStatusMap.get(this.xcomponentId);
      if (!result) {
        reject();
        return;
      }
      LogUtils.getInstance().LOGI("stop id:" + this.xcomponentId)
      this.CONTROL_PlayStatus = PlayStatus.INIT;
      this.stopProgressTask();
      await this.mIjkMediaPlayer.stopAsync();
      await this.mIjkMediaPlayer.releaseAsync();
      resolve();
    });
  }

  private seekTo(value: string) {
    this.mIjkMediaPlayer.seekTo(value);

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
    this.videoUrl = this.videoUrls[this.curIndex];
    this.stop().then(() => {
      this.startPlayOrResumePlay()
    });
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
    let isRecord = this.mIjkMediaPlayer.isRecord()
    if (isRecord) {
      prompt.showToast({
        message: $r('app.string.recordIng')
      });
      return
    }
    this.recordSaveFilePath = getContext(this).cacheDir + "/record.mp4";
    let result = this.mIjkMediaPlayer.startRecord(this.recordSaveFilePath);
    prompt.showToast({
      message: result ? $r('app.string.start_record_success') : $r('app.string.start_record_failed')
    });
  }

  private stopRecord(isShowTip: boolean) {
    let isRecord = this.mIjkMediaPlayer.isRecord()
    if (!isRecord) {
      if (isShowTip) {
        prompt.showToast({
          message: $r('app.string.record_not_enabled')
        });
      }
      return
    }
    this.recordProgressVisible = Visibility.Visible;
    this.mIjkMediaPlayer.stopRecord().then((result) => {
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
    this.mIjkMediaPlayer.screenshot(saveFilePath).then((result) => {
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
