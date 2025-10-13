export type ToolkitConfig = {
  key: string;
  toolkitClass: string;
  enabled: boolean;
  config: Record<string, unknown>;
};

export type PromptConfig = {
  key: string;
  name: string;
  enabled: boolean;
  instructionCount: number;
};

export type AgnoConfiguration = {
  toolkits: ToolkitConfig[];
  prompts: PromptConfig[];
};

export type UpdateToolkitEnabledInput = {
  key: string;
  enabled: boolean;
};

export type UpdatePromptEnabledInput = {
  key: string;
  enabled: boolean;
};
