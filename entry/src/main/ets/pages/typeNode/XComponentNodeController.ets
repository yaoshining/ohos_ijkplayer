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

import { FrameNode, NodeController, typeNode } from '@kit.ArkUI';
import { LogUtils } from '@ohos/ijkplayer';
import { PipManager } from './PipManager';
import { XComponentLoadCallBack } from './XComponentLoadCallBack';

export class XComponentNodeController extends NodeController {
  xcomponentNode: typeNode.XComponent | null = null;
  private node: FrameNode | null = null;

  makeNode(uiContext: UIContext): FrameNode | null {
    if (!this.node) {
      this.node = new FrameNode(uiContext);
      this.node.commonAttribute.width('100%');
      this.node.commonAttribute.backgroundColor(Color.Black);
    }
    return this.node;
  }

  addNode() {
    if (this.node !== null && this.node !== undefined) {
        LogUtils.getInstance().LOGI("addNode");
        this.xcomponentNode?.getParent()?.removeChild(this.xcomponentNode);
        this.node.appendChild(this.xcomponentNode);
    }
  }

  removeNode() {
    if (this.node !== null && this.node !== undefined) {
      LogUtils.getInstance().LOGI("removeNode");
      this.node.removeChild(this.xcomponentNode);
    }
  }

  createXComponentNode(context: UIContext, xcomponentId: string, xcomponentLoadCallBack: XComponentLoadCallBack) {
    let options: XComponentOptions = {
      type: XComponentType.SURFACE,
      controller: PipManager.getInstance().getXComponentController()
    };
    this.xcomponentNode = typeNode.createNode(context, "XComponent", options);
    this.xcomponentNode.commonAttribute.id(xcomponentId);
    this.xcomponentNode.attribute.width('100%');
    this.xcomponentNode.initialize({
      id: xcomponentId,
      type: XComponentType.SURFACE,
      libraryname: 'ijkplayer_napi',
    }).onLoad((context: object) => {
      if (xcomponentLoadCallBack) {
        xcomponentLoadCallBack.onLoadSuccess(context);
      }
    });
  }

  getXComponentNode(): typeNode.XComponent | null {
    return this.xcomponentNode;
  }
}