export class RunGate {
  private active: boolean = false;
  private generation: number = 0;
  begin(): number { this.active = true; this.generation++; return this.generation; }
  cancel(): void { this.active = false; this.generation++; }
  accepts(token: number, ready: boolean): boolean { return this.active && ready && token === this.generation; }
}
