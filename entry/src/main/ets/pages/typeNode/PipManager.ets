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
import { PiPWindow, typeNode } from '@kit.ArkUI';
import { BusinessError } from '@kit.BasicServicesKit';
import { XComponentNodeController } from './XComponentNodeController';
import { XComponentLoadCallBack } from './XComponentLoadCallBack';
import { PipOnActionEventCallBack } from './PipOnActionEventCallBack';
import { PlayStatus } from '../../common/PlayStatus';
import { IjkMediaPlayer, LogUtils } from '@ohos/ijkplayer';

const TAG = 'PipManager';

export class PipManager {
  private static instance: PipManager = new PipManager();
  private xcNodeController: XComponentNodeController;
  private mXComponentController: XComponentController;
  private lifeCycleCallback: Set<Function> = new Set();
  private onActionEventCallBack: PipOnActionEventCallBack | undefined;
  pipController?: PiPWindow.PiPController = undefined;
  isHasStartPip: boolean = false;
  videoWidth: string = '100%';
  videoAspectRatio: number = 1;
  xcomponentId: string = "";
  playStatusMap: Map<string, PlayStatus | undefined> = new Map();
  ijkMediaPlayer: IjkMediaPlayer = IjkMediaPlayer.getInstance();
  volume: number = 1.0;
  isPlayDone: boolean = false;
  videoUrl: string = "";
  pipState: PiPWindow.PiPState = PiPWindow.PiPState.STOPPED

  public static getInstance(): PipManager {
    return PipManager.instance;
  }


  constructor() {
    this.xcNodeController = new XComponentNodeController();
    this.mXComponentController = new XComponentController();
  }


  public registerLifecycleCallback(callBack: Function) {
    this.lifeCycleCallback.add(callBack);
  }


  public unRegisterLifecycleCallback(callBack: Function): void {
    this.lifeCycleCallback.delete(callBack);
  }


  getXComponentNode(): typeNode.XComponent | null {
    return this.xcNodeController.getXComponentNode();
  }


  onActionEvent(control: PiPWindow.ControlEventParam) {
    if (this.onActionEventCallBack) {
      this.onActionEventCallBack.onActionEvent(control);
    }
    LogUtils.getInstance().LOGI('onActionEvent, controlType:' + control.controlType + ', status' + control.status);
  }


  onStateChange(state: PiPWindow.PiPState, reason: string) {
    let curState: string = '';
    this.pipState = state;
    if (this.lifeCycleCallback !== null) {
      this.lifeCycleCallback.forEach((fun) => {
        fun(state)
      });
    }
    switch (state) {
      case PiPWindow.PiPState.ABOUT_TO_START:
        curState = "ABOUT_TO_START";
        break;
      case PiPWindow.PiPState.STARTED:
        curState = "STARTED";
        break;
      case PiPWindow.PiPState.ABOUT_TO_STOP:
        curState = "ABOUT_TO_STOP";
        break;
      case PiPWindow.PiPState.STOPPED:
        curState = "STOPPED";
        break;
      case PiPWindow.PiPState.ABOUT_TO_RESTORE:
        curState = "ABOUT_TO_RESTORE";
        break;
      case PiPWindow.PiPState.ERROR:
        curState = "ERROR";
        break;
      default:
        break;
    }
    LogUtils.getInstance().LOGI(`[${TAG}] onStateChange: ${curState}, reason: ${reason}`);
  }

  unregisterPipStateChangeListener() {
    LogUtils.getInstance().LOGI(`${TAG} aboutToDisappear`)
    this.pipController?.off('stateChange');
    this.pipController?.off('controlEvent');
  }

  getXComponentController(): XComponentController {
    return this.mXComponentController;
  }

  initPipController(ctx: Context) {
    if (this.pipController !== null && this.pipController != undefined) {
      LogUtils.getInstance().error("initPipController pipController null");
      return;
    }
    if (!PiPWindow.isPiPEnabled()) {
      LogUtils.getInstance().error(`picture in picture disabled for current OS`);
      return;
    }
    let config: PiPWindow.PiPConfiguration = {
      context: ctx,
      componentController: this.getXComponentController(),
      templateType: PiPWindow.PiPTemplateType.VIDEO_PLAY,
      contentWidth: 1920,
      contentHeight: 1080,
    };
    let promise: Promise<PiPWindow.PiPController> = PiPWindow.create(config, this.getXComponentNode());
    promise.then((controller: PiPWindow.PiPController) => {
      LogUtils.getInstance().LOGI("initPipController PiPWindow.create success");
      this.pipController = controller;
      this.pipController.on('stateChange', (state: PiPWindow.PiPState, reason: string) => {
        this.onStateChange(state, reason);
      });
      this.pipController.on('controlEvent', (control: PiPWindow.ControlEventParam) => {
        this.onActionEvent(control);
      });
    }).catch((err: BusinessError) => {
      LogUtils.getInstance().error(`Failed to create pip controller. Cause:${err.code}, message:${err.message}`);
    });
  }


  startPip(callback: PipOnActionEventCallBack) {
    this.onActionEventCallBack = callback;
    this.isHasStartPip = true;
    this.pipController?.startPiP().then(() => {
      LogUtils.getInstance().LOGI(`Succeeded in starting pip.`);
    }).catch((err: BusinessError) => {
      LogUtils.getInstance().error(`Failed to start pip. Cause:${err.code}, message:${err.message}`);
    });
  }

  stopPip() {
    this.isHasStartPip = false;
    if (this.pipController) {
      let promise: Promise<void> = this.pipController.stopPiP();
      promise.then(() => {
        this.pipController = undefined;
        LogUtils.getInstance().LOGI(`Succeeded in stopping pip.`);
      }).catch((err: BusinessError) => {
        this.pipController = undefined;
        LogUtils.getInstance().error(`Failed to stop pip. Cause:${err.code}, message:${err.message}`);
      });
    }
  }


  getNodeController(): XComponentNodeController {
    LogUtils.getInstance().LOGI(`getNodeController.`);
    return this.xcNodeController;
  }


  setAutoStart(autoStart: boolean): void {
    this.pipController?.setAutoStartEnabled(autoStart);
  }


  removeNode(): void {
    this.xcNodeController.removeNode();
  }


  addNode(): void {
    this.xcNodeController.addNode();
  }

  createXComponentNode(context: UIContext, xcomponentId: string, xcomponentLoadCallBack: XComponentLoadCallBack) {
    this.xcNodeController.createXComponentNode(context, xcomponentId, xcomponentLoadCallBack);
  }
}