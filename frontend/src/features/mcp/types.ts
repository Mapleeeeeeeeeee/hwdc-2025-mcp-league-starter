export type McpServer = {
  name: string;
  description?: string | null;
  connected: boolean;
  enabled: boolean;
  functionCount: number;
  functions: string[];
};

export type McpServersSnapshot = {
  initialized: boolean;
  servers: McpServer[];
};

export type McpToolSelection = {
  server: string;
  functions?: string[];
};
