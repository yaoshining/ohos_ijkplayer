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
import router from '@ohos.router'

@Entry
@Component
struct IjkVideoPlayerTypeNodeIndex {
  build() {
    Column() {
      Button($r('app.string.router'))
        .margin({ bottom: 20 })
        .width(200)
        .onClick(() => {
          router.pushUrl({ url: 'pages/typeNode/IjkVideoPlayerTypeNodePage', params: {
            videoUrl: "https://1251542705.vod2.myqcloud.com/4a8d9c67vodtransgzp1251542705/203109c63270835013529449619/v.f1419907.mp4"
          } })
        })
      Button($r('app.string.Navigation'))
        .width(200)
        .margin({ bottom: 20 })
        .onClick(() => {
          router.pushUrl({ url: 'pages/typeNode/IjkVideoPlayerTypeNodeNavigationExample' })
        })

      Button($r('app.string.PictureInPicture'))
        .width(200)
        .onClick(() => {
          router.pushUrl({ url: 'pages/typeNode/IjkVideoPlayerPipIndex' })
        })
    }
    .width('100%')
    .height('100%')
    .backgroundColor(Color.Gray)
    .justifyContent(FlexAlign.Center)
  }
}