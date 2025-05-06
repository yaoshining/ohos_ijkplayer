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

export class IjkplayerMapManager {

  private static instance: IjkplayerMapManager;

  private constructor() {
  }

  public static getInstance(): IjkplayerMapManager {
    if (!IjkplayerMapManager.instance) {
      IjkplayerMapManager.instance = new IjkplayerMapManager();
    }
    return IjkplayerMapManager.instance;
  }

  //xcomponentId唯一标识
  private static id: number = 1;

  //记录是否播放过的状态
  private _playStatusMap: Map<string, boolean> = new Map();

  //记录是否销毁过的状态
  private _destroyStatusMap: Map<string, boolean> = new Map();

  public get playStatusMap(): Map<string, boolean> {
    return this._playStatusMap;
  }

  public get destroyStatusMap(): Map<string, boolean> {
    return this._destroyStatusMap;
  }

  public clearAll() {
    this._playStatusMap.clear();
    this._destroyStatusMap.clear()
  }

  public static generateId(): number {
    return this.id = this.id + 1;
  }
}