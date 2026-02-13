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

@Entry
@Component
struct indexPage {
  build() {
    Column() {
      Button($r('app.string.video_demo'))
        .margin({ bottom: 20 })
        .width(200)
        .onClick(() => {
          this.getUIContext().getRouter().pushUrl({ url: 'pages/SampleVideoListPage' })
        })
      Button($r('app.string.audio_demo'))
        .width(200)
        .margin({ bottom: 20 })
        .onClick(() => {
          this.getUIContext().getRouter().pushUrl({ url: 'pages/SampleAudioListPage' })
        })
      Button($r('app.string.Navigation'))
        .width(200)
        .margin({ bottom: 20 })
        .onClick(() => {
          this.getUIContext().getRouter().pushUrl({ url: 'pages/IjkVideoPlayerNavigationExample' })
        })
      Button($r('app.string.typeNode'))
        .width(200)
        .margin({ bottom: 20 })
        .onClick(() => {
          this.getUIContext().getRouter().pushUrl({ url: 'pages/typeNode/IjkVideoPlayerTypeNodeIndex' })
        })
      Button('10Bit Video Player')
        .width(200)
        .margin({ bottom: 20 })
        .onClick(() => {
          // 跳转到10bit视频播放页面
          this.getUIContext().getRouter().pushUrl({ url: 'pages/IjkVideo10BitPlayerPage' })
        })
    }
    .width('100%')
    .height('100%')
    .backgroundColor(Color.Gray)
    .justifyContent(FlexAlign.Center)
  }
}