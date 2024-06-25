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

import { describe, it, expect } from '@ohos/hypium'
import { IjkMediaPlayer, LogUtils,
  OnBufferingUpdateListener,
  OnCompletionListener,
  OnErrorListener, OnInfoListener, OnPreparedListener,
  OnSeekCompleteListener,
  OnTimedTextListener} from "@ohos/ijkplayer";
import prompt from '@ohos.promptAction';

let mIjkMediaPlayer = IjkMediaPlayer.getInstance();

export default function abilityTest() {
  describe('ActsAbilityTest',  () =>{
    it('initIjkPlayer', 0,  () => {
      mIjkMediaPlayer.setAudioId('audioIjkId');
      //设置debug模式
      mIjkMediaPlayer.setDebug(true);
      //初始化配置
      mIjkMediaPlayer.native_setup();
      //设置视频源
      mIjkMediaPlayer.setDataSource("https://1251542705.vod2.myqcloud.com/4a8d9c67vodtransgzp1251542705/203109c63270835013529449619/v.f1419907.mp4");
      //设置视频源http请求头
      let headers = new Map([
        ["user_agent", "Mozilla/5.0 BiliDroid/7.30.0 (bbcallen@gmail.com)"],
        ["referer", "https://www.bilibili.com"]
      ]);
      mIjkMediaPlayer.setDataSourceHeader(headers);
      //使用精确寻帧 例如，拖动播放后，会寻找最近的关键帧进行播放，很有可能关键帧的位置不是拖动后的位置，而是较前的位置.可以设置这个参数来解决问题
      mIjkMediaPlayer.setOption(IjkMediaPlayer.OPT_CATEGORY_PLAYER, "enable-accurate-seek", "1");
      //预读数据的缓冲区大小
      mIjkMediaPlayer.setOption(IjkMediaPlayer.OPT_CATEGORY_PLAYER, "max-buffer-size", "102400");
      //停止预读的最小帧数
      mIjkMediaPlayer.setOption(IjkMediaPlayer.OPT_CATEGORY_PLAYER, "min-frames", "100");
      //启动预加载
      mIjkMediaPlayer.setOption(IjkMediaPlayer.OPT_CATEGORY_PLAYER, "start-on-prepared", "1");
      // 设置无缓冲，这是播放器的缓冲区，有数据就播放
      mIjkMediaPlayer.setOption(IjkMediaPlayer.OPT_CATEGORY_PLAYER, "packet-buffering", "0");
      //跳帧处理,放CPU处理较慢时，进行跳帧处理，保证播放流程，画面和声音同步
      mIjkMediaPlayer.setOption(IjkMediaPlayer.OPT_CATEGORY_PLAYER, "framedrop", "5");
      // 最大缓冲cache是3s， 有时候网络波动，会突然在短时间内收到好几秒的数据
      // 因此需要播放器丢包，才不会累积延时
      // 这个和第三个参数packet-buffering无关。
      mIjkMediaPlayer.setOption(IjkMediaPlayer.OPT_CATEGORY_PLAYER, "max_cached_duration", "3000");
      // 无限制收流
      mIjkMediaPlayer.setOption(IjkMediaPlayer.OPT_CATEGORY_PLAYER, "infbuf", "1");
      mIjkMediaPlayer.setOptionLong(IjkMediaPlayer.OPT_CATEGORY_PLAYER, "infbuf", "1")
      // 屏幕常亮
      mIjkMediaPlayer.setScreenOnWhilePlaying(true);
      // 设置超时
      mIjkMediaPlayer.setOption(IjkMediaPlayer.OPT_CATEGORY_FORMAT, "timeout", "10000000");
      mIjkMediaPlayer.setOption(IjkMediaPlayer.OPT_CATEGORY_FORMAT, "connect_timeout", "10000000");
      mIjkMediaPlayer.setOption(IjkMediaPlayer.OPT_CATEGORY_FORMAT, "addrinfo_timeout", "10000000");
      mIjkMediaPlayer.setOption(IjkMediaPlayer.OPT_CATEGORY_FORMAT, "dns_cache_timeout", "10000000");
      // 设置音量
      // mIjkMediaPlayer.setVolume("0.5", "0.5");
      // 变速播放
      mIjkMediaPlayer.setOption(IjkMediaPlayer.OPT_CATEGORY_PLAYER, "soundtouch", "1");
      mIjkMediaPlayer.setSpeed('1f');
      let Speed = mIjkMediaPlayer.getSpeed()
      LogUtils.getInstance().LOGI('getSpeed--' + Speed)
      //是否开启循环播放
      mIjkMediaPlayer.setLoopCount(true);
      let mOnPreparedListener: OnPreparedListener = {
        onPrepared: () => {
          LogUtils.getInstance().LOGI("setOnPreparedListener-->go");
        }
      }
      mIjkMediaPlayer.setOnPreparedListener(mOnPreparedListener);

      let mOnTimedTextListener: OnTimedTextListener = {
        onTimedText: () => {
        }
      }
      mIjkMediaPlayer.setOnTimedTextListener(mOnTimedTextListener)

      let mOnCompletionListener: OnCompletionListener = {
        onCompletion: () => {
          LogUtils.getInstance().LOGI("OnCompletionListener-->go")
        }
      }
      mIjkMediaPlayer.setOnCompletionListener(mOnCompletionListener);

      let mOnBufferingUpdateListener: OnBufferingUpdateListener = {
        onBufferingUpdate: (percent: number) => {
          LogUtils.getInstance().LOGI("OnBufferingUpdateListener-->go:" + percent);
          let MediaInfo = mIjkMediaPlayer.getMediaInfo()
          LogUtils.getInstance().LOGI('getMediaInfo---' + MediaInfo);

          let Looping = mIjkMediaPlayer.isLooping()
          LogUtils.getInstance().LOGI('isLooping---' + Looping);
        }
      }
      mIjkMediaPlayer.setOnBufferingUpdateListener(mOnBufferingUpdateListener);

      let mOnSeekCompleteListener: OnSeekCompleteListener = {
        onSeekComplete: () => {
          LogUtils.getInstance().LOGI("OnSeekCompleteListener-->go");
        }
      }
      mIjkMediaPlayer.setOnSeekCompleteListener(mOnSeekCompleteListener);

      let mOnInfoListener: OnInfoListener = {
        onInfo: (what: number, extra: number) => {
          LogUtils.getInstance().LOGI("OnInfoListener-->go:" + what + "===" + extra);
        }
      }
      mIjkMediaPlayer.setOnInfoListener(mOnInfoListener);


      let mOnErrorListener: OnErrorListener = {
        onError: (what: number, extra: number) => {
          LogUtils.getInstance().LOGI("OnErrorListener-->go:" + what + "===" + extra)
          prompt.showToast({
            message: "亲，音频播放异常，系统开小差咯"
          });
        }
      }

      mIjkMediaPlayer.setOnErrorListener(mOnErrorListener);

      mIjkMediaPlayer.setMessageListener();

      mIjkMediaPlayer.prepareAsync();

      mIjkMediaPlayer.start();

      expect(mIjkMediaPlayer.getSpeed()).assertEqual('1.000000')
    })

    it('getMediaInfo', 0,  () => {
      let MediaInfo = mIjkMediaPlayer.getMediaInfo();
      expect(typeof MediaInfo).assertEqual('object')
    })

    it('isLooping', 0,  () => {
      let loopFlag = mIjkMediaPlayer.isLooping();
      expect(loopFlag).assertTrue();
    })

    it('isPlaying', 0,  () => {
      let isPlaying = mIjkMediaPlayer.isPlaying();
      expect(isPlaying).assertFalse();
    })

    it('pause', 0,  () => {
      mIjkMediaPlayer.pause();;
      expect(mIjkMediaPlayer.isPlaying()).assertFalse();
    })

    it('stop', 0,  () => {
      mIjkMediaPlayer.stop();
      expect(mIjkMediaPlayer.isPlaying()).assertFalse();
    })

    it('reset', 0,  () => {
      mIjkMediaPlayer.reset();
      expect(mIjkMediaPlayer.isPlaying()).assertFalse();
    })

    it('release', 0,  () => {
      mIjkMediaPlayer.release();
      expect(mIjkMediaPlayer.isPlaying()).assertFalse();
    })

    it('seekTo', 0,  () => {
      let position = mIjkMediaPlayer.getCurrentPosition();
      let seekValue = 3 * (mIjkMediaPlayer.getDuration() / 100);
      mIjkMediaPlayer.seekTo(seekValue.toString());
      expect(mIjkMediaPlayer.isPlaying()).assertFalse();
    })
  })
}