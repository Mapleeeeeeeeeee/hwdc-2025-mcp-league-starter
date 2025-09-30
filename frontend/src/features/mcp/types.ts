export type McpServer = {
  name: string;
  description?: string;
  connected: boolean;
  enabled: boolean;
  functionCount: number;
  functions: string[];
};

export type McpServersSnapshot = {
  initialized: boolean;
  servers: McpServer[];
};
