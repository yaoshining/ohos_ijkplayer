import { common } from '@kit.AbilityKit';
import { fileIo as fs } from '@kit.CoreFileKit';
import probe from 'libphase22.so';

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

  private write(path: string, content: string | ArrayBuffer): void {
    const f = fs.openSync(path, fs.OpenMode.CREATE | fs.OpenMode.READ_WRITE | fs.OpenMode.TRUNC);
    try { fs.writeSync(f.fd, content); } finally { fs.closeSync(f); }
  }
  private async prepare(): Promise<void> {
    const context = this.getUIContext().getHostContext() as common.UIAbilityContext;
    this.root = context.filesDir + '/phase22';
    for (const name of ['', '/state', '/state/private', '/state/state', '/state/lock', '/cache', '/cache/demux', '/resources', '/resources/fonts', '/resources/cjk']) {
      if (!fs.accessSync(this.root + name)) { fs.mkdirSync(this.root + name); }
    }
    const names: string[] = ['font1.ttf', 'Mplus1p-Regular.ttf', 'h264.mp4', 'hevc.mp4', 'subtitle.ass'];
    const destinations: string[] = ['/resources/fonts/font1.ttf', '/resources/cjk/Mplus1p-Regular.ttf', '/h264.mp4', '/hevc.mp4', '/subtitle.ass'];
    for (let i = 0; i < names.length; i++) {
      const data = await context.resourceManager.getRawFileContent(names[i]);
      this.write(this.root + destinations[i], data.buffer as ArrayBuffer);
    }
    this.write(this.root + '/smb.conf', '[global]\nclient min protocol = SMB2\n');
    this.write(this.root + '/other.conf', '[global]\nclient min protocol = SMB2\n');
    this.prepared = true;
    this.maybeStart();
  }
  aboutToAppear(): void { this.prepare().catch((e: Error) => { this.status = '准备失败: ' + e.message; }); }
  aboutToDisappear(): void { probe.stop(); }
  private maybeStart(): void {
    if (this.prepared && this.ready && !this.started) {
      this.started = true;
      this.runAll().catch((e: Error) => { this.status = '诊断异常: ' + e.message; });
    }
  }
  private async runAll(): Promise<void> {
    const modes: string[] = ['init', 'repeat', 'conflict', 'gl-sw', 'gl-h264', 'gl-hevc', 'vk-h264', 'vk-hevc'];
    for (const mode of modes) {
      this.status = '正在验证 ' + mode + '（独立应用）';
      const result = await probe.run(this.root, this.controller.getXComponentSurfaceId(), 1280, 720, mode);
      console.info('Phase22 ' + mode + ': ' + result);
      this.write(this.root + '/' + mode + '-result.txt', result);
      this.status = mode + ': ' + result;
    }
    this.status = '本轮已结束，日志等待核验。这里不自动宣称验收通过。';
  }
  build() {
    Column() {
      Text(this.status).fontSize(18).width('100%').height(90).fontColor(Color.White);
      if (this.surfaceVisible) {
        XComponent({ id: 'phase22-' + this.generation, type: XComponentType.SURFACE, controller: this.controller })
          .width(1280).height(720)
          .onLoad(() => { this.ready = true; this.maybeStart(); })
          .onDestroy(() => { this.ready = false; probe.stop(); });
      }
      Button('停止独立诊断').onClick(() => { probe.stop(); this.status = '已请求停止当前场景'; });
    }.width('100%').height('100%').backgroundColor(Color.Black);
  }
}
