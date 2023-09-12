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
export declare class ijkplayerNapi {
  _nativeOpenlog();
  _setDataSource(url:string);
  _setOption(category:string,key:string,value:string);
  _setOptionLong(category:string,key:string,value:string);
  _prepareAsync();
  _start();
  _stop();
  _pause();
  _reset();
  _release();
  _seekTo(msec:string);
  _isPlaying();
  _getDuration();
  _setMessageListener(messageCallBack:Function);
  _getCurrentPosition();
  _getAudioSessionId();
  _setPropertyFloat(property: string, value: string);
  _getPropertyFloat(property: string, value: string);
  _setPropertyLong(property: string, value: string);
  _getPropertyLong(property: string, value: string);
  _setVolume(leftVolume: string, rightVolume: string);
  _setLoopCount(loopCount: string);
  _getLoopCount();
  _setStreamSelected(stream: string, select: string);
  _getVideoCodecInfo();
  _getAudioCodecInfo();
  _getMediaMeta();
  _native_setup();
}