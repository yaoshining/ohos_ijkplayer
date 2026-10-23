export class RecreationGuard {
  private generation: number = 0;
  private active: boolean = false;
  begin(): void { this.generation++; this.active = true; }
  cancel(): void { this.generation++; this.active = false; }
  private valid(token: number): boolean { return this.active && token === this.generation; }
  async perform(stop: () => Promise<void>, remove: () => void, remount: () => void, delay: () => Promise<void>): Promise<void> {
    const token = this.generation;
    if (!this.valid(token)) { return; }
    await stop();
    if (!this.valid(token)) { return; }
    remove();
    await delay();
    if (!this.valid(token)) { return; }
    remount();
  }
}
