import { AbilityConstant, UIAbility, Want } from '@kit.AbilityKit';
import { window } from '@kit.ArkUI';
import { fileIo as fs } from '@kit.CoreFileKit';
import probe from 'libphase22.so';
import { Timeline, Event } from '../lifecycle/Timeline';

export default class EntryAbility extends UIAbility {
  private stage: window.WindowStage | undefined = undefined;
  private main: window.Window | undefined = undefined;
  private stageCallback: ((e: window.WindowStageLifecycleEventType) => void) | undefined = undefined;
  private windowCallback: ((e: window.WindowEventType) => void) | undefined = undefined;
  private generation: number = 0;
  onCreate(_want: Want, _launchParam: AbilityConstant.LaunchParam): void {
    const root = this.context.filesDir + '/phase30-consumer';
    if (!fs.accessSync(root)) { fs.mkdirSync(root); }
    const mode = _want.parameters?.['phase30Mode'];
    const allowed: string[] = ['vk-inject-release', 'vk-inject-wait', 'vk-inject-hang', 'vk-handoff-switch', 'vk-concurrent-switch', 'vk-pq', 'gl-pq', 'gl-pq-sw', 'normal-repeat', 'no-registration', 'callback-hang', 'ui-block', 'logger-hang'];
    const selected = typeof mode === 'string' && allowed.indexOf(mode) >= 0 ? mode : '';
    const plan = fs.openSync(root + '/run-plan.txt', fs.OpenMode.CREATE | fs.OpenMode.READ_WRITE | fs.OpenMode.TRUNC);
    try { fs.writeSync(plan.fd, selected); } finally { fs.closeSync(plan); }
    Timeline.live = probe.beginTimeline(root);
    Timeline.record(Event.AbilityCreate);
  }
  onForeground(): void { Timeline.record(Event.AbilityForeground); if (this.main && probe.terminalState() === 0) { Timeline.keepAwake(this.main, this.generation, true); } }
  onBackground(): void { Timeline.record(Event.AbilityBackground); }
  onDestroy(): void { Timeline.record(Event.AbilityDestroy); if (probe.terminalState() === 0) { probe.stop(); } }
  onWindowStageCreate(stage: window.WindowStage): void {
    this.stage = stage; Timeline.stage = stage;
    const gen = ++this.generation; Timeline.stageGeneration = gen;
    Timeline.record(Event.StageCreate, gen);
    this.stageCallback = (e: window.WindowStageLifecycleEventType): void => {
      if (e === window.WindowStageLifecycleEventType.SHOWN) { Timeline.record(Event.StageShown, gen); }
      else if (e === window.WindowStageLifecycleEventType.RESUMED) { Timeline.record(Event.StageResumed, gen); }
      else if (e === window.WindowStageLifecycleEventType.PAUSED) { Timeline.record(Event.StagePaused, gen); }
      else if (e === window.WindowStageLifecycleEventType.HIDDEN) { Timeline.record(Event.StageHidden, gen); }
    };
    this.windowCallback = (e: window.WindowEventType): void => {
      if (e === window.WindowEventType.WINDOW_ACTIVE) { Timeline.record(Event.WindowActive, gen); }
      else if (e === window.WindowEventType.WINDOW_INACTIVE) { Timeline.record(Event.WindowInactive, gen); }
    };
    try { stage.on('windowStageLifecycleEvent', this.stageCallback); } catch (_) { Timeline.record(Event.SubscriptionFailed, gen, 1); }
    try {
      this.main = stage.getMainWindowSync();
      this.main.on('windowEvent', this.windowCallback);
      if (probe.terminalState() === 0) { Timeline.keepAwake(this.main, gen, true); }
    } catch (_) { Timeline.record(Event.SubscriptionFailed, gen, 2); }
    stage.loadContent('pages/Index', (err) => { if (err.code) { Timeline.record(Event.LoggingError, gen, 3); } });
  }
  onWindowStageDestroy(): void {
    Timeline.record(Event.StageDestroy, this.generation);
    try { if (this.stage && this.stageCallback) { this.stage.off('windowStageLifecycleEvent', this.stageCallback); } }
    catch (_) { Timeline.record(Event.SubscriptionFailed, this.generation, 5); }
    try { if (this.main && this.windowCallback) { this.main.off('windowEvent', this.windowCallback); } }
    catch (_) { Timeline.record(Event.SubscriptionFailed, this.generation, 6); }
    this.stage = undefined; this.main = undefined; Timeline.stage = undefined;
  }
}
