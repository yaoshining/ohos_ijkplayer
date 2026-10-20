import { window, display } from '@kit.ArkUI';
import { common } from '@kit.AbilityKit';
import { fileIo as fs } from '@kit.CoreFileKit';
import probe from 'libphase22.so';
import { surfacePixels } from '../lifecycle/SurfaceSize';
import { RunGate } from '../lifecycle/RunGate';
import { RecreationGuard } from '../lifecycle/RecreationGuard';

@Entry
@Component
struct Index {
  @State status: string = 'Phase24：HDR 与长播诊断';
  @State surfaceVisible: boolean = true;
  @State generation: number = 1;
  private controller: XComponentController = new XComponentController();
  private root: string = '';
  private prepared: boolean = false;
  private ready: boolean = false;
  private started: boolean = false;
  private cycles: number = 0;
  private gate: RunGate = new RunGate();
  private recreation: RecreationGuard = new RecreationGuard();

  private write(path: string, content: string | ArrayBuffer): void {
    const f = fs.openSync(path, fs.OpenMode.CREATE | fs.OpenMode.READ_WRITE | fs.OpenMode.TRUNC);
    try { fs.writeSync(f.fd, content); } finally { fs.closeSync(f); }
  }
  private async prepare(): Promise<void> {
    const context = this.getUIContext().getHostContext() as common.UIAbilityContext;
    this.root = context.filesDir + '/phase24';
    for (const name of ['', '/state', '/state/private', '/state/state', '/state/lock', '/cache', '/cache/demux', '/resources', '/resources/fonts', '/resources/cjk']) {
      if (!fs.accessSync(this.root + name)) { fs.mkdirSync(this.root + name); }
    }
    const names: string[] = ['font1.ttf', 'Mplus1p-Regular.ttf', 'pq-bounded.mp4', 'hlg-bounded.mp4', 'sdr-bounded.mp4', 'pq2-bounded.mp4'];
    const destinations: string[] = ['/resources/fonts/font1.ttf', '/resources/cjk/Mplus1p-Regular.ttf', '/pq-bounded.mp4', '/hlg-bounded.mp4', '/sdr-bounded.mp4', '/pq2-bounded.mp4'];
    for (let i = 0; i < names.length; i++) {
      const data = await context.resourceManager.getRawFileContent(names[i]);
      this.write(this.root + destinations[i], data.buffer as ArrayBuffer);
    }
    this.write(this.root + '/smb.conf', '[global]\nclient min protocol = SMB2_02\n');
    this.write(this.root + '/other.conf', '[global]\nclient min protocol = SMB2_02\n');
    const d = display.getDefaultDisplaySync();
    this.write(this.root + '/display.json', JSON.stringify({ id: d.id, width: d.width, height: d.height, hdrFormats: d.hdrFormats, colorSpaces: d.colorSpaces }));
    console.info('Phase24 display id=' + d.id + ' pixels=' + d.width + 'x' + d.height + ' hdr=' + JSON.stringify(d.hdrFormats) + ' colors=' + JSON.stringify(d.colorSpaces));
    this.prepared = true;
    this.maybeStart();
  }
  aboutToAppear(): void { this.recreation.begin(); this.prepare().catch((e: Error) => { this.status = '准备失败: ' + e.message; }); }
  private releaseKeepAwake(): void {
    const context = this.getUIContext().getHostContext() as common.UIAbilityContext;
    window.getLastWindow(context).then((w: window.Window) => w.setWindowKeepScreenOn(false)).catch((e: Error) => { console.error('Phase22 release keep-awake: ' + e.message); });
  }
  aboutToDisappear(): void { this.recreation.cancel(); this.gate.cancel(); probe.stop(); this.releaseKeepAwake(); }
  private maybeStart(): void {
    if (this.prepared && this.ready && !this.started) {
      this.started = true;
      (this.cycles > 0 ? this.runRecreated(this.gate.begin()) : this.runAll(this.gate.begin())).catch((e: Error) => { this.status = '诊断异常: ' + e.message; console.error('Phase22 scheduling error: ' + e.message); });
    }
  }
  private async runProbe(mode: string): Promise<string> {
    const rect = this.controller.getXComponentSurfaceRect();
    const size = surfacePixels(rect);
    console.info('Phase23 surface-pixels=' + size.width + 'x' + size.height + ' mode=' + mode);
    return probe.run(this.root, this.controller.getXComponentSurfaceId(), size.width, size.height, mode);
  }
  private async runAll(token: number): Promise<void> {
    let modes: string[] = ['gl-sdr', 'vk-sdr', 'gl-pq', 'vk-pq', 'gl-hlg', 'vk-hlg', 'gl-sdr-sw', 'vk-sdr-sw', 'gl-pq-sw', 'vk-pq-sw', 'gl-hlg-sw', 'vk-hlg-sw', 'gl-switch', 'vk-switch'];
    if (fs.accessSync(this.root + '/run-plan.txt')) {
      modes = fs.readTextSync(this.root + '/run-plan.txt').trim().split('\n');
    }
    const allowed: string[] = ['gl-sdr', 'vk-sdr', 'gl-pq', 'vk-pq', 'gl-hlg', 'vk-hlg', 'gl-sdr-sw', 'vk-sdr-sw', 'gl-pq-sw', 'vk-pq-sw', 'gl-hlg-sw', 'vk-hlg-sw', 'gl-switch', 'vk-switch', 'gl-nas-short', 'vk-nas-short', 'gl-nas-long', 'vk-nas-long', 'gl-pq-rgb10', 'gl-hlg-rgb10', 'gl-sdr-rgb10'];
    for (const mode of modes) {
      if (!this.gate.accepts(token, this.ready)) { return; }
      if (allowed.indexOf(mode) < 0) { this.status = '场景配置无效'; return; }
      this.status = 'Phase24 正在运行 ' + mode;
      const result = await this.runProbe(mode);
      if (!this.gate.accepts(token, this.ready)) { return; }
      console.info('Phase24 ' + mode + ': ' + result);
      this.write(this.root + '/' + mode + '-result.txt', result);
      this.status = mode + ': ' + result;
    }
    this.status = 'Phase24 本组诊断结束，结果等待逐项审核';
    this.releaseKeepAwake();
  }
  private async interruptAndRecreate(token: number): Promise<void> {
    if (!this.gate.accepts(token, this.ready)) { return; }
    await this.recreation.perform(async () => {
      this.status = 'Surface 主动停止与重建 ' + this.cycles;
      const timer = setTimeout(() => { probe.stop(); }, 2000);
      let result: string = '';
      try { result = await this.runProbe(this.cycles === 0 ? 'gl-h264' : 'gl-sw'); }
      finally { clearTimeout(timer); }
      console.info('Phase22 surface-stop-' + this.cycles + ': ' + result);
      this.write(this.root + '/surface-stop-' + this.cycles + '.txt', result);
    }, () => {
      this.gate.cancel(); this.ready = false; this.surfaceVisible = false;
    }, () => {
      this.controller = new XComponentController(); this.generation++; this.cycles++;
      this.started = false; this.surfaceVisible = true;
    }, () => new Promise<void>((resolve) => { setTimeout(resolve, 500); }));
  }
  private async remountMatrix(token: number): Promise<void> {
    if (!this.gate.accepts(token, this.ready)) { return; }
    await this.recreation.perform(async () => {}, () => {
      this.gate.cancel(); this.ready = false; this.surfaceVisible = false;
    }, () => {
      this.controller = new XComponentController(); this.generation++; this.cycles++;
      this.started = false; this.surfaceVisible = true;
    }, () => new Promise<void>((resolve) => { setTimeout(resolve, 500); }));
  }
  private async runRecreated(token: number): Promise<void> {
    if (!this.gate.accepts(token, this.ready)) { return; }
    const id = this.controller.getXComponentSurfaceId();
    console.info('Phase23 recreated generation=' + this.generation + ' surface=' + id);
    const mode: string = this.cycles === 1 ? 'gl-h264' : 'gl-sw';
    const result = await this.runProbe(mode);
    if (!this.gate.accepts(token, this.ready)) { return; }
    console.info('Phase23 recreated-' + this.cycles + ': ' + result);
    this.write(this.root + '/recreated-' + this.cycles + '.txt', result);
    if (this.cycles < 2) { await this.remountMatrix(token); }
    else { this.status = 'Phase23 实际像素尺寸GL/VK对照完成'; this.releaseKeepAwake(); }
  }
  build() {
    Column() {
      Text(this.status).fontSize(18).width('100%').height(65).fontColor(Color.White);
      if (this.surfaceVisible) {
        XComponent({ id: 'phase22-' + this.generation, type: XComponentType.SURFACE, controller: this.controller })
          .width(960).height(540)
          .onLoad(() => { this.ready = true; this.maybeStart(); })
          .onDestroy(() => { this.ready = false; this.gate.cancel(); probe.stop(); });
      }
      Button('停止独立诊断').onClick(() => { this.recreation.cancel(); this.gate.cancel(); probe.stop(); this.status = '已请求停止当前场景'; this.releaseKeepAwake(); });
    }.width('100%').height('100%').backgroundColor(Color.Black);
  }
}
