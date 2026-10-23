import probe from 'libphase22.so';
import { window } from '@kit.ArkUI';
export enum Event {
  AbilityCreate=8, AbilityForeground=9, AbilityBackground=10, AbilityDestroy=11,
  StageCreate=12, StageShown=13, StageResumed=14, StagePaused=15, StageHidden=16, StageDestroy=17,
  WindowActive=18, WindowInactive=19, SurfaceCreate=20, SurfaceDestroy=21, Late=22,
  SubscriptionFailed=23, Operator=24, LoggingError=25, FaultDelay=26, KeepAwakeRequest=29, KeepAwakeSuccess=30, KeepAwakeReadback=31, KeepAwakeFailure=32
}
export class Timeline {
  static stage: window.WindowStage | undefined = undefined;
  static live: boolean = false;
  static stageGeneration: number = 0;
  static record(e: Event, generation: number = 0, key: number = 0): boolean {
    return Timeline.live && probe.event(e, generation, key);
  }
  static async keepAwake(w: window.Window, gen: number, enabled: boolean): Promise<boolean> {
    if (!Timeline.live || (enabled && probe.terminalState() !== 0)) { return false; }
    Timeline.record(Event.KeepAwakeRequest, gen, enabled ? 1 : 0);
    try {
      await w.setWindowKeepScreenOn(enabled);
      if (enabled && probe.terminalState() !== 0) {
        await w.setWindowKeepScreenOn(false);
        const corrected = !w.getWindowProperties().isKeepScreenOn;
        probe.terminalMark(corrected ? 21 : 22);
        return false;
      }
      Timeline.record(Event.KeepAwakeSuccess, gen, enabled ? 1 : 0);
      const actual = w.getWindowProperties().isKeepScreenOn;
      Timeline.record(Event.KeepAwakeReadback, gen, actual ? 1 : 0);
      if (actual !== enabled) { Timeline.record(Event.KeepAwakeFailure, gen, 2); }
      return actual === enabled;
    } catch (_) { Timeline.record(Event.KeepAwakeFailure, gen, 1); return false; }
  }
  static async focusExperiment(): Promise<void> {
    const stage = Timeline.stage;
    const generation = Timeline.stageGeneration;
    if (!stage || !Timeline.live || probe.terminalState() !== 0) { return; }
    Timeline.record(Event.Operator, generation, 1);
    let child: window.Window | undefined = undefined;
    try {
      child = await stage.createSubWindow('phase25-focus');
      if (Timeline.stage !== stage || !Timeline.live || probe.terminalState() !== 0) { await child.destroyWindow(); return; }
      await child.loadContent('pages/Focus');
      if (probe.terminalState() !== 0) { return; }
      await child.setWindowFocusable(true);
      if (probe.terminalState() !== 0) { return; }
      await child.showWindow();
      await new Promise<void>((resolve) => { setTimeout(resolve, 3000); });
    } catch (_) { Timeline.record(Event.SubscriptionFailed, generation, 4); }
    finally { if (child) { try { await child.destroyWindow(); } catch (_) { Timeline.record(Event.LoggingError, generation, 4); } } }
  }
}
