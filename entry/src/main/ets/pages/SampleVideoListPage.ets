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
import fileio from '@ohos.fileio';

@Entry
@Component
struct SampleVideoListPage {
  build() {

    Flex({ direction: FlexDirection.Column, alignItems: ItemAlign.Start, justifyContent: FlexAlign.Start }) {
      Flex({ direction: FlexDirection.Column, alignItems: ItemAlign.Center, justifyContent: FlexAlign.Center }) {
        Text("ijkplayer播放器示例")
          .fontSize(26)
          .fontColor(Color.White)
          .margin(10)
          .fontWeight(FontWeight.Bold)
      }.height(100).width('100%').backgroundColor(Color.Black)

      List({ space: 20, initialIndex: 0 }) {

        ListItem() {
          Text("测试地址1：http://1251017968.vod2.myqcloud.com/3eb04eefvodtransgzp1251017968/8782b1285285890810009576163/v.f30.mp4")
            .fontSize(20)
            .fontWeight(FontWeight.Bold)
            .fontColor(Color.Black)
            .margin(10)
            .onClick(() => {
              router.push({ url: "pages/IjkVideoPlayerPage", params: {
                videoUrl: "http://1251017968.vod2.myqcloud.com/3eb04eefvodtransgzp1251017968/8782b1285285890810009576163/v.f30.mp4"
              } });
            })
        }

        ListItem() {

          Text("测试地址2：https://1251017968.vod2.myqcloud.com/3eb04eefvodtransgzp1251017968/8782b1285285890810009576163/v.f30.mp4")
            .fontSize(20)
            .fontColor(Color.Black)
            .fontWeight(FontWeight.Bold)
            .margin(10)
            .onClick(() => {
              router.push({
                url: "pages/IjkVideoPlayerPage",
                params: {
                  videoUrl: "https://1251017968.vod2.myqcloud.com/3eb04eefvodtransgzp1251017968/8782b1285285890810009576163/v.f30.mp4"
                }
              });
            })
        }

        ListItem() {

          Text("测试地址3：http://newcntv.qcloudcdn.com/asp/hls/main/0303000a/3/default/a15b46e2313d46aaa70cf15399f6a196/main.m3u8?maxbr=2048")
            .fontSize(20)
            .fontColor(Color.Black)
            .fontWeight(FontWeight.Bold)
            .margin(10)
            .onClick(() => {
              router.push({
                url: "pages/IjkVideoPlayerPage",
                params: {
                  videoUrl: "http://newcntv.qcloudcdn.com/asp/hls/main/0303000a/3/default/a15b46e2313d46aaa70cf15399f6a196/main.m3u8?maxbr=2048"
                }
              });
            })
        }

        ListItem() {

          Text("测试地址4：https://dvod.300hu.com/vod/product/179b797b-a38a-4e70-9529-defa11593dbb/afd6438205424934aa57352b93a1fc86.m3u8")
            .fontSize(20)
            .fontColor(Color.Black)
            .fontWeight(FontWeight.Bold)
            .margin(10)
            .onClick(() => {
              router.push({
                url: "pages/IjkVideoPlayerPage",
                params: {
                  videoUrl: "https://dvod.300hu.com/vod/product/179b797b-a38a-4e70-9529-defa11593dbb/afd6438205424934aa57352b93a1fc86.m3u8"
                }
              });
            })
        }

        ListItem() {

          Text("测试地址5：http://hls.nntv.cn/nnlive/NNTV_METRO_A.m3u8")
            .fontSize(20)
            .fontColor(Color.Black)
            .fontWeight(FontWeight.Bold)
            .margin(10)
            .onClick(() => {
              router.push({
                url: "pages/IjkVideoPlayerPage",
                params: {
                  videoUrl: "http://hls.nntv.cn/nnlive/NNTV_METRO_A.m3u8"
                }
              });
            })
        }

        ListItem() {
          Text("测试地址6：http://music.163.com/song/media/outer/url?id=447925558.mp3")
            .fontSize(20)
            .fontColor(Color.Black)
            .fontWeight(FontWeight.Bold)
            .margin(10)
            .onClick(() => {
              router.push({
                url: "pages/IjkVideoPlayerPage",
                params: {
                  videoUrl: "http://music.163.com/song/media/outer/url?id=447925558.mp3"
                }
              });
            })
        }


        ListItem() {
          Text("测试地址7：https://sf1-hscdn-tos.pstatp.com/obj/media-fe/xgplayer_doc_video/flv/xgplayer-demo-720p.flv")
            .fontSize(20)
            .fontColor(Color.Black)
            .fontWeight(FontWeight.Bold)
            .margin(10)
            .onClick(() => {
              router.push({
                url: "pages/IjkVideoPlayerPage",
                params: {
                  videoUrl: "https://sf1-hscdn-tos.pstatp.com/obj/media-fe/xgplayer_doc_video/flv/xgplayer-demo-720p.flv"
                }
              });
            })
        }
      }
    }
  }

  typedArrayToBuffer(array: Uint8Array): ArrayBuffer {
    return array.buffer.slice(array.byteOffset, array.byteLength + array.byteOffset)
  }

  writeFile(path: string, content: ArrayBuffer | string) {
    try {
      let fd = fileio.openSync(path, 0o102, 0o666)
      fileio.ftruncateSync(fd)
      fileio.writeSync(fd, content)
      fileio.fsyncSync(fd)
      fileio.closeSync(fd)
    } catch (e) {
    }
  }
}