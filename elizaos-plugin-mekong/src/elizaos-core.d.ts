/** Minimal local typings for @elizaos/core — enough to compile the plugin standalone. */
declare module '@elizaos/core' {
  export interface ActionExample {
    user: string;
    content: { text: string; action?: string };
  }
  export interface ActionResult {
    text: string;
    success: boolean;
    error?: Error;
    data?: unknown;
  }
  export interface Memory {
    content: { text?: string; action?: string; [k: string]: unknown };
    [k: string]: unknown;
  }
  export interface HandlerCallback {
    (response: { text: string; error?: boolean; [k: string]: unknown }): Promise<void>;
  }
  export interface Action {
    name: string;
    similes?: string[];
    description: string;
    validate: (
      runtime: IAgentRuntime,
      message: Memory,
      state?: unknown
    ) => Promise<boolean>;
    handler: (
      runtime: IAgentRuntime,
      message: Memory,
      state?: unknown,
      options?: unknown,
      callback?: HandlerCallback
    ) => Promise<ActionResult>;
    examples: ActionExample[][];
  }
  export interface IAgentRuntime {
    getSetting(key: string): string | undefined;
    logger?: { info?(...a: unknown[]): void; warn?(...a: unknown[]): void; error?(...a: unknown[]): void };
    [k: string]: unknown;
  }
  export interface Plugin {
    name: string;
    description: string;
    actions?: Action[];
    evaluators?: unknown[];
    providers?: unknown[];
    init?: (config: Record<string, string>, runtime: IAgentRuntime) => Promise<void>;
    [k: string]: unknown;
  }
}
