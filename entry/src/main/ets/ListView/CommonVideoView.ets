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

class PlayerListenerClass implements PlayerListener{
  onPlay(): void {
  }

  onStop(): void {
  }

  onPause(): void {
  }

  onError(): void {
  }

  onUpdate(current: number, duration: number): void {
  }

  onComplete(): void {
  }
}
@Component
export struct CommonVideoView {
  public videoSource: VideoSource | null = null;
  private pic = $r('app.media.icon');
  private xComponentContext: object | null = null;
  private player: VideoPlayer = new VideoPlayer();
  private isInit: boolean = false;
  private xComponentId = "xid" + Math.random();
  @State isPlaying: boolean = false;

  build() {
    Flex({ direction: FlexDirection.Column, alignItems: ItemAlign.Auto, justifyContent: FlexAlign.Start }) {
      Stack() {
        XComponent({
          id: this.videoSource?.title + this.xComponentId,
          type: 'surface',
          libraryname: 'ijkplayer_napi'
        })
          .onLoad((context) => {
            if (context) {
              this.xComponentContext = context;
            }
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

      Flex({ direction: FlexDirection.Row, alignItems: ItemAlign.Center, justifyContent: FlexAlign.Start }) {
        Button($r('app.string.Play'))
          .onClick(() => {
            this.play();
          })
          .width('400px')
          .height('80px')
          .margin('15px')
        Button($r('app.string.Pause'))
          .onClick(() => {
            if(this.player != null) {
              this.player.pause()
            }
          })
          .width('400px')
          .height('80px')
          .margin('15px')

        Button($r('app.string.destroy'))
          .onClick(() => {
            this.release();
          })
          .width('400px')
          .height('80px')
          .margin('15px')
      }
    }
  }

  initPlayer(): void {
    this.player = new VideoPlayer();
    let listener = new PlayerListenerClass();
    this.player.setContext(this.xComponentContext!, this.videoSource?.title + this.xComponentId)
      .setVideoSource(this.videoSource!)
      .setListener(listener);
  }

  play(): void {
    if (!this.isInit || this.player == null) {
      this.isInit = true;
      this.initPlayer();
    }
    this.isPlaying = true;
    this.player?.play();
  }

  stop(): void {
    if (this.player != null) {
      this.player.pause();
    }
    this.isPlaying = false;
  }

  release() {
    if(this.player != null) {
      this.player.stop();
      this.player.release();
      this.isInit = false;
    }
  }
}