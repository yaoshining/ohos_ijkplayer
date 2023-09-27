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

import { PlayerListener } from './PlayerListener'
import { VideoPlayer } from './VideoPlayer'
import { VideoSource } from './VideoSource'

@Component
export struct CommonVideoView {
  private videoSource: VideoSource
  private pic = $r('app.media.icon');
  private xComponentContext: object;
  private player: VideoPlayer;
  private isInit: boolean = false;
  private xComponentId = "xid" + Math.random();
  @State isPlaying: boolean = false;

  build() {
    Stack() {
      XComponent({
        id: this.xComponentId,
        type: 'surface',
        libraryname: 'ijkplayer_napi'
      })
        .onLoad((context) => {
          this.xComponentContext = context;
        })
        .onDestroy(() => {

        })
        .width('100%')
        .height('100%')
        .onClick(() => {
          this.stop();
        })
      Image(this.pic)
        .width('100%')
        .height('100%')
        .visibility(this.isPlaying ? Visibility.None : Visibility.Visible)
        .onClick(() => {
          this.play();
        })
      Image($r('app.media.icon_replay'))
        .width(45).height(45)
        .visibility(this.isPlaying ? Visibility.None : Visibility.Visible)
        .onClick(() => {
          this.play();
        })
    }.width('100%').height('100%')
  }

  initPlayer() {
    this.player = VideoPlayer.getInstance()
    let listener: PlayerListener = {
      onPlay() {

      },
      onStop() {

      },
      onPause() {

      },
      onError() {

      },
      onUpdate(current: number, duration: number) {

      },
      onComplete() {

      }
    }
    this.player.setContext(this.xComponentContext)
      .setVideoSource(this.videoSource)
      .setListener(listener);
  }

  play() {
    if (!this.isInit || this.player == null) {
      this.isInit = true;
      this.initPlayer();
    }
    this.isPlaying = true;
    this.player.play();
  }

  stop() {
    if (this.player != null) {
      this.player.pause();
    }
    this.isPlaying = false;
  }
}