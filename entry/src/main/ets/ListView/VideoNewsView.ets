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

import router from '@ohos.router';
import { CommonVideoView } from './CommonVideoView';
import { VideoSource } from './VideoSource';

@Preview
@Component
export default struct VideoNewsView {
  @State title: string = "";
  private radio: number =  1.77;
  private testUrl: string = "https://1251542705.vod2.myqcloud.com/4a8d9c67vodtransgzp1251542705/203109c63270835013529449619/v.f1419907.mp4";

  build() {
    Column() {
      CommonVideoView({
        videoSource: new VideoSource(this.testUrl, '', this.title)
      }).width('100%').aspectRatio(this.radio)
        .borderRadius(10)
    }.width('100%').height('40%').padding({ 'right': 14, 'left': 14 })
  }
}