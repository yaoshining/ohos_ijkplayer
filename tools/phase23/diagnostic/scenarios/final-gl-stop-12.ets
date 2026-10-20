import { window } from '@kit.ArkUI';
import { common } from '@kit.AbilityKit';
import { fileIo as fs } from '@kit.CoreFileKit';
import probe from 'libphase22.so';
import { RunGate } from '../lifecycle/RunGate';
import { RecreationGuard } from '../lifecycle/RecreationGuard';

@Entry
@Component
struct Index {
  @State status: string = 'Phase22 独立诊断：准备资源';
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
    this.root = context.filesDir + '/phase23';
    for (const name of ['', '/state', '/state/private', '/state/state', '/state/lock', '/cache', '/cache/demux', '/resources', '/resources/fonts', '/resources/cjk']) {
      if (!fs.accessSync(this.root + name)) { fs.mkdirSync(this.root + name); }
    }
    const names: string[] = ['font1.ttf', 'Mplus1p-Regular.ttf', 'h264.mp4', 'hevc.mp4', 'subtitle.ass', 'smb-test.txt', 'smb-wrong.txt'];
    const destinations: string[] = ['/resources/fonts/font1.ttf', '/resources/cjk/Mplus1p-Regular.ttf', '/h264.mp4', '/hevc.mp4', '/subtitle.ass', '/smb-test.txt', '/smb-wrong.txt'];
    for (let i = 0; i < names.length; i++) {
      const data = await context.resourceManager.getRawFileContent(names[i]);
      this.write(this.root + destinations[i], data.buffer as ArrayBuffer);
    }
    this.write(this.root + '/smb.conf', '[global]\nclient min protocol = SMB2_02\n');
    this.write(this.root + '/other.conf', '[global]\nclient min protocol = SMB2_02\n');
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
  private async runAll(token: number): Promise<void> {
    const modes: string[] = ['gl-h264'];
    for (const mode of modes) {
      if (!this.gate.accepts(token, this.ready)) { return; }
      this.status = '正在验证 ' + mode + '（独立应用）';
      const result = await probe.run(this.root, this.controller.getXComponentSurfaceId(), 960, 540, mode);
      if (!this.gate.accepts(token, this.ready)) { return; }
      console.info('Phase22 ' + mode + ': ' + result);
      this.write(this.root + '/' + mode + '-result.txt', result);
      this.status = mode + ': ' + result;
    }
    await this.interruptAndRecreate(token);
  }
  private async interruptAndRecreate(token: number): Promise<void> {
    if (!this.gate.accepts(token, this.ready)) { return; }
    await this.recreation.perform(async () => {
      this.status = 'Surface 主动停止与重建 ' + this.cycles;
      const timer = setTimeout(() => { probe.stop(); }, 2000);
      let result: string = '';
      try { result = await probe.run(this.root, this.controller.getXComponentSurfaceId(), 960, 540, this.cycles === 0 ? 'gl-h264' : 'gl-sw'); }
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
    const mode: string = 'gl-sw';
    const result = await probe.run(this.root, id, 960, 540, mode);
    if (!this.gate.accepts(token, this.ready)) { return; }
    console.info('Phase23 recreated-' + this.cycles + ': ' + result);
    this.write(this.root + '/recreated-' + this.cycles + '.txt', result);
    if (this.cycles < 2) { await this.interruptAndRecreate(token); }
    else { this.status = 'Phase23 GL硬软解主动停止及新Surface恢复完成'; this.releaseKeepAwake(); }
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
