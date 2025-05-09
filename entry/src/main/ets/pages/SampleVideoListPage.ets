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

import router from '@ohos.router';
import VideoNewsView from '../ListView/VideoNewsView';
import { IjkplayerMapManager } from './IjkplayerMapManager';

@Entry
@Component
struct SampleVideoListPage {
  private items: Array<string> = ['1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '11', '12', '13'];

  build() {

    Flex({ direction: FlexDirection.Column, alignItems: ItemAlign.Start, justifyContent: FlexAlign.Start }) {
      Flex({ direction: FlexDirection.Column, alignItems: ItemAlign.Center, justifyContent: FlexAlign.Center }) {
        Text($r('app.string.ijkplayer_Example'))
          .fontSize(26)
          .fontColor(Color.White)
          .margin(10)
          .fontWeight(FontWeight.Bold)
      }.height(100).width('100%').backgroundColor(Color.Black)

      List({ space: 20, initialIndex: 0 }) {
        ListItem() {
          Text(getContext().resourceManager.getStringByNameSync("Test_address") +
            "https://1251542705.vod2.myqcloud.com/4a8d9c67vodtransgzp1251542705/203109c63270835013529449619/v.f1419907.mp4")
            .fontSize(20)
            .fontWeight(FontWeight.Bold)
            .fontColor(Color.Black)
            .margin(10)
            .onClick(() => {
              router.pushUrl({
                url: "pages/IjkVideoPlayerPage", params: {
                  videoUrl: "https://1251542705.vod2.myqcloud.com/4a8d9c67vodtransgzp1251542705/203109c63270835013529449619/v.f1419907.mp4"
                }
              });
            })
        }

      }.height('30%')

      List({ space: 20 }) {
        ForEach(this.items, (title: string) => {
          ListItem() {
            VideoNewsView({ title: title })
          }
        })
      }.margin({ top: 30 })
    }
  }

  aboutToDisappear(): void {
    IjkplayerMapManager.getInstance().clearAll();
  }
}