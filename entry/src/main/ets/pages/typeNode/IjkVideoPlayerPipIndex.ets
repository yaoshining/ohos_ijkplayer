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
import { PipManager } from './PipManager';
import { PiPWindow, router, Router } from '@kit.ArkUI';
import { LogUtils } from '@ohos/ijkplayer';

@Entry
@Component
struct IjkVideoPlayerPipIndex {
  private pageRouter: Router | null = null;
  private callback: Function = (state: PiPWindow.PiPState) => {
    LogUtils.getInstance().LOGI(`pipStateChange: state ${state}`);
    if (state === PiPWindow.PiPState.ABOUT_TO_START) {
      this.pageRouter?.back();
    } else if (state === PiPWindow.PiPState.ABOUT_TO_STOP) {
      PipManager.getInstance().addNode();
    } else if (state === PiPWindow.PiPState.ABOUT_TO_RESTORE) {
      this.jumpNext();
    }
  };

  aboutToAppear(): void {
    this.pageRouter = this.getUIContext().getRouter();
    PipManager.getInstance().registerLifecycleCallback(this.callback);
  }

  aboutToDisappear(): void {
    PipManager.getInstance().unregisterPipStateChangeListener();
    PipManager.getInstance().unRegisterLifecycleCallback(this.callback);
  }

  jumpNext(): void {
    let topPage = this.pageRouter?.getState();
    if (topPage !== undefined && ('pages/typeNode/IjkVideoPlayerPipPage'.toString() === topPage.path + topPage.name)) {
      return;
    }
    this.pageRouter?.pushUrl({
      params: {
        videoUrl: "https://1251542705.vod2.myqcloud.com/4a8d9c67vodtransgzp1251542705/203109c63270835013529449619/v.f1419907.mp4"
      },
      url: 'pages/typeNode/IjkVideoPlayerPipPage'
    }, router.RouterMode.Standard);
  }

  build() {
    Row() {
      Column() {
        Text('Main Page')
          .fontSize(50)
          .fontWeight(FontWeight.Bold)


        Button('Jump Next')
          .onClick(() => {
            this.jumpNext();
          })
          .margin({ top: 16, bottom: 16 })
      }
      .width('100%')
    }
    .height('100%')
  }
}