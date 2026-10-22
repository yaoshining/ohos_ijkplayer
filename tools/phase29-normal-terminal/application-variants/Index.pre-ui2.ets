import { window, display } from '@kit.ArkUI';
import { common } from '@kit.AbilityKit';
import { fileIo as fs } from '@kit.CoreFileKit';
import probe from 'libphase22.so';
import { surfacePixels } from '../lifecycle/SurfaceSize';
import { Timeline, Event } from '../lifecycle/Timeline';
class SurfaceController extends XComponentController {
  readonly generation: number;
  private live: boolean = false;
  private ready: (generation: number) => void;
  constructor(generation: number, ready: (generation: number) => void) { super(); this.generation = generation; this.ready = ready; }
  onSurfaceCreated(_id: string): void { this.live = Timeline.record(Event.SurfaceCreate, this.generation); }
  onSurfaceChanged(_id: string, rect: SurfaceRect): void { if (this.live && rect.surfaceWidth > 0 && rect.surfaceHeight > 0) { this.ready(this.generation); } }
  onSurfaceDestroyed(_id: string): void { this.live = false; Timeline.record(Event.SurfaceDestroy, this.generation); }
}
@Entry
@Component
struct Index {
  @State status: string = 'Phase28：等待场景配置';
  @State surfaceVisible: boolean = true;
  @State generation: number = 1;
  private controller: SurfaceController = new SurfaceController(1, (g: number) => { this.surfaceReady(g); });
  private root: string = '';
  private prepared: boolean = false;
  private ready: boolean = false;
  private alive: boolean = true;
  private started: boolean = false;
  private active: Promise<string> | undefined = undefined;
  private terminalTimer: number = -1;
  private terminating: boolean = false;
  private currentMode: string = '';
  private async checkTerminal(): Promise<void> {
    if (this.terminating || probe.terminalState() === 0) { return; }
    this.terminating = true;
    this.status = '播放器遇到不可恢复故障，应用将退出，请重新打开。';
    probe.terminalMark(1);
    if (this.currentMode === 'ui-block') { const end = Date.now() + 5000; while (Date.now() < end) {} return; }
    const context = this.getUIContext().getHostContext() as common.UIAbilityContext;
    try {
      const w = await window.getLastWindow(context);
      await w.setWindowKeepScreenOn(false);
      probe.terminalMark(w.getWindowProperties().isKeepScreenOn ? 12 : 2);
    } catch (_) { probe.terminalMark(13); }
    if (this.currentMode === 'callback-hang' || this.currentMode === 'logger-hang') { return; }
    await new Promise<void>((resolve) => { setTimeout(resolve, 800); });
    // 异常主动终止，不承诺完整生命周期清理；独立native deadline始终计时。
    probe.terminalMark(3);
    context.getApplicationContext().killAllProcesses(true).catch(() => { probe.terminalMark(14); });
  }
  private write(path: string, content: string | ArrayBuffer): void {
    const f = fs.openSync(path, fs.OpenMode.CREATE | fs.OpenMode.READ_WRITE | fs.OpenMode.TRUNC);
    try { fs.writeSync(f.fd, content); } finally { fs.closeSync(f); }
  }
  private async prepare(): Promise<void> {
    const context = this.getUIContext().getHostContext() as common.UIAbilityContext;
    this.root = context.filesDir + '/phase29-terminal';
    for (const name of ['', '/state', '/state/private', '/state/state', '/state/lock', '/cache', '/cache/demux', '/resources', '/resources/fonts', '/resources/cjk']) {
      if (!fs.accessSync(this.root + name)) { fs.mkdirSync(this.root + name); }
    }
    const names: string[] = ['font1.ttf', 'Mplus1p-Regular.ttf', 'pq-bounded.mp4', 'hlg-bounded.mp4', 'sdr-bounded.mp4', 'pq2-bounded.mp4', 'pqchange-bounded.mp4'];
    const destinations: string[] = ['/resources/fonts/font1.ttf', '/resources/cjk/Mplus1p-Regular.ttf', '/pq-bounded.mp4', '/hlg-bounded.mp4', '/sdr-bounded.mp4', '/pq2-bounded.mp4', '/pqchange-bounded.mp4'];
    for (let i = 0; i < names.length; i++) {
      const data = await context.resourceManager.getRawFileContent(names[i]);
      if (!this.alive) { return; }
      this.write(this.root + destinations[i], data.buffer as ArrayBuffer);
    }
    // A launch parameter selects one bounded diagnostic scenario. Empty by default.
    if (!fs.accessSync(this.root + '/run-plan.txt')) { this.write(this.root + '/run-plan.txt', ''); }
    this.write(this.root + '/smb.conf', '[global]\nclient min protocol = SMB2_02\n');
    this.write(this.root + '/other.conf', '[global]\nclient min protocol = SMB2_02\n');
    const d = display.getDefaultDisplaySync();
    this.write(this.root + '/display.json', JSON.stringify({ id: d.id, width: d.width, height: d.height, hdrFormats: d.hdrFormats, colorSpaces: d.colorSpaces }));
    console.info('Phase28 display id=' + d.id + ' pixels=' + d.width + 'x' + d.height + ' hdr=' + JSON.stringify(d.hdrFormats) + ' colors=' + JSON.stringify(d.colorSpaces));
    if (!this.alive) { return; }
    this.prepared = true;
    this.maybeStart();
  }
  aboutToAppear(): void { this.terminalTimer = setInterval(() => { this.checkTerminal(); }, 50); this.prepare().catch(() => { this.status = '准备失败'; Timeline.record(Event.LoggingError, 0, 10); }); }
  aboutToDisappear(): void { this.alive = false; if (this.terminalTimer >= 0) { clearInterval(this.terminalTimer); } if (probe.terminalState() === 0) { probe.stop(); } }
  private surfaceReady(g: number): void { if (!this.alive || g !== this.generation) { Timeline.record(Event.Late, g); return; } this.ready = true; this.maybeStart(); }
  private maybeStart(): void {
    if (this.terminating || probe.terminalState() !== 0 || !this.alive || !this.prepared || !this.ready || this.started) { return; }
    this.started = true;
    this.runAll().catch(() => { this.status = '场景失败'; Timeline.record(Event.LoggingError, this.generation, 11); });
  }
  private async runAll(): Promise<void> {
    if (!fs.accessSync(this.root + '/run-plan.txt')) { this.status = '请先配置独立场景'; this.started = false; return; }
    const selected = fs.readTextSync(this.root + '/run-plan.txt').trim();
    this.write(this.root + '/run-plan.txt', '');
    if (!selected) { this.status = '未配置场景'; await this.finish(); return; }
    const modes = selected.split('\n');
    if (modes.length !== 1) { this.status = '每个进程只允许一个场景'; await this.finish(); return; }
    const allowed: string[] = ['vk-inject-release', 'vk-inject-wait', 'vk-inject-hang', 'vk-consumer-switch', 'vk-pq', 'gl-pq', 'gl-pq-sw', 'normal-repeat', 'no-registration', 'callback-hang', 'ui-block', 'logger-hang'];
    this.currentMode = selected;
    if (!probe.configureTerminal(this.root, selected)) { this.status = '接管未注册，已拒绝播放和软件回退'; await this.finish(); return; }
    const runs = selected === 'normal-repeat' ? ['vk-pq', 'vk-pq'] : modes;
    const gen = this.generation;
    for (const mode of runs) {
      if (this.terminating || probe.terminalState() !== 0 || !this.alive || gen !== this.generation) { return; }
      if (allowed.indexOf(mode) < 0) { this.status = '配置无效'; return; }
      const size = surfacePixels(this.controller.getXComponentSurfaceRect());
      this.status = 'Phase28 正在运行 ' + mode;
      const active: Promise<string> = probe.run(this.root, this.controller.getXComponentSurfaceId(), size.width, size.height, mode);
      this.active = active;
      const result = await active; this.active = undefined;
      if (this.terminating || probe.terminalState() !== 0 || !this.alive || gen !== this.generation) { return; }
      this.write(this.root + '/' + mode + '-result.txt', result); this.status = result;
    }
    this.status = '场景完成';
    await this.finish();
  }
  private async finish(): Promise<void> {
    if (this.terminating || probe.terminalState() !== 0 || !Timeline.live) { return; }
    Timeline.record(Event.Operator, this.generation, 2); probe.stop();
    if (this.active) { await this.active; }
    const context = this.getUIContext().getHostContext() as common.UIAbilityContext;
    let keepScreen = 'unknown';
    try {
      const w = await window.getLastWindow(context);
      const ok = await Timeline.keepAwake(w, Timeline.stageGeneration, false);
      keepScreen = ok ? 'false' : 'readback-mismatch';
    } catch (_) { Timeline.record(Event.KeepAwakeFailure, Timeline.stageGeneration, 3); keepScreen = 'error'; }
    if (probe.closeTimeline()) { Timeline.live = false; this.status = '会话已封口 keepScreen=' + keepScreen; }
  }
  private async recreate(): Promise<void> {
    if (this.terminating || probe.terminalState() !== 0 || !Timeline.live) { return; }
    Timeline.record(Event.Operator, this.generation, 3); probe.stop();
    if (this.active) { await this.active; }
    if (!this.alive) { return; }
    this.ready = false; this.surfaceVisible = false;
    await new Promise<void>((resolve) => { setTimeout(resolve, 500); });
    if (!this.alive) { return; }
    this.generation++; this.controller = new SurfaceController(this.generation, (g: number) => { this.surfaceReady(g); });
    this.started = false; this.surfaceVisible = true;
  }
  build() {
    Column() {
      Text(this.status).fontSize(18).height(65).fontColor(Color.White);
      if (this.surfaceVisible) { XComponent({ id: 'phase25-' + this.generation, type: XComponentType.SURFACE, controller: this.controller }).width(960).height(540); }
      Row() {
        Button('焦点短实验').id('p27-focus').onClick(() => { Timeline.focusExperiment(); });
        Button('重建 Surface').id('p27-recreate').onClick(() => { this.recreate(); });
        Button('结束会话').id('p27-finish').onClick(() => { this.finish(); });
      }
    }.width('100%').height('100%').backgroundColor(Color.Black);
  }
}
