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
  private title: string;
  private radio: 1.77;
  private testUrl = "http://devimages.apple.com.edgekey.net/streaming/examples/bipbop_4x3/bipbop_4x3_variant.m3u8";

  build() {
    Column() {
      CommonVideoView({
        videoSource: new VideoSource(this.testUrl, '')
      }).width('100%').aspectRatio(this.radio)
        .borderRadius(10)
    }.width('100%').height('30%').padding({ 'right': 14, 'left': 14 })
  }
}