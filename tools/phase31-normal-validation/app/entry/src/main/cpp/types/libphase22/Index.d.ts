export const run: (root: string, surface: string, width: number, height: number, mode: string) => Promise<string>;
export const stop: () => void;

export const beginTimeline: (root: string) => boolean;
export const event: (event: number, generation: number, key: number) => boolean;
export const closeTimeline: () => boolean;

export const configureTerminal: (root: string, mode: string) => boolean;
export const terminalState: () => number;
export const terminalMark: (code: number) => void;
