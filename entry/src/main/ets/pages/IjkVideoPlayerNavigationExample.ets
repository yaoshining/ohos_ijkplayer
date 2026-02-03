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

import { IjkplayerMapManager } from './IjkplayerMapManager';
import fileio from '@ohos.fileio';
import { fileIo } from '@kit.CoreFileKit';
import { Config7z, Uncompress } from '@ohos/oh7zip';

@Entry
@Component
struct IjkVideoPlayerNavigationExample {
  @Provide('pathInfos') pathInfos: NavPathStack = new NavPathStack();
  private listArray: Array<string> = ['IjkVideoPlayer','IjkAudioPlayer'];
  private videoUrl: string = 'https://1251542705.vod2.myqcloud.com/4a8d9c67vodtransgzp1251542705/203109c63270835013529449619/v.f1419907.mp4';

  build() {
    Column() {
      Navigation(this.pathInfos) {
        List({ space: 12, initialIndex: 0 }) {
          ForEach(this.listArray, (item: string) => {
            ListItem() {
              Row() {
                Column() {
                  Text(item)
                    .fontSize(16)
                    .margin({ bottom: 5 })
                }
                .alignItems(HorizontalAlign.Start)
                Blank()
                Row()
                  .width(12)
                  .height(12)
                  .margin({ right: 15 })
                  .border({
                    width: { top: 2, right: 2 },
                    color: 0xcccccc
                  })
                  .rotate({ angle: 45 })
              }
              .borderRadius(15)
              .shadow({ radius: 100, color: '#ededed' })
              .width('90%')
              .alignItems(VerticalAlign.Center)
              .padding({ left: 15, top: 15, bottom: 15 })
              .backgroundColor(Color.White)
            }
            .width('100%')
            .onClick(() => {
              this.pathInfos.pushPathByName(`${item}`, this.videoUrl)
            })
          }, (item: string): string => item)
        }
        .listDirection(Axis.Vertical)
        .edgeEffect(EdgeEffect.Spring)
        .sticky(StickyStyle.Header)
        .chainAnimation(false)
        .width('100%')
      }
      .width('100%')
      .mode(NavigationMode.Auto)
      .title('Navigation')
    }
    .size({ width: '100%', height: '100%' })
    .backgroundColor(0xf4f4f5)
  }

  aboutToAppear(): void {
    let context = getContext(this);
    let srcPath = context.resourceDir + '/app';
    let destPath = context.filesDir + '/app';
    try {
      if (!fileIo.accessSync(destPath)) {
        fileIo.mkdirSync(destPath);
      }
    } catch (error) {
      console.error(`出现异常: ${error}`)
      return;
    }
    let uncompress: Uncompress = new Uncompress()
    let config: Config7z = {
      src: srcPath + '/4k.part1.rar',
      dst: destPath
    }
    uncompress.extractAsync(config)
      .then((result: number) => {
        if (result != 0) {
          console.error('解压失败')
          return
        }
        console.info('解压成功')
      })
      .catch(() =>{
        console.error(`解压失败`);
      });
  }

  aboutToDisappear(): void {
    IjkplayerMapManager.getInstance().clearAll();
  }
}