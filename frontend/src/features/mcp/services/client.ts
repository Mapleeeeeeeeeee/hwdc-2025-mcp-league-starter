import { apiRequest } from "@/lib/api/api-client";

import type { McpServer, McpServersSnapshot } from "../types";

type McpServerDto = {
  name: string;
  description?: string | null;
  connected: boolean;
  enabled: boolean;
  function_count: number;
  functions: string[];
};

type ListServersResponseDto = {
  initialized: boolean;
  servers: McpServerDto[];
};

function mapServer(dto: McpServerDto): McpServer {
  return {
    name: dto.name,
    description: dto.description ?? undefined,
    connected: dto.connected,
    enabled: dto.enabled,
    functionCount: dto.function_count,
    functions: dto.functions,
  };
}

function mapServersSnapshot(dto: ListServersResponseDto): McpServersSnapshot {
  return {
    initialized: dto.initialized,
    servers: dto.servers.map(mapServer),
  };
}

const LIST_SERVERS_PATH = "/api/v1/mcp/servers";

export async function listServers(): Promise<McpServersSnapshot> {
  const data = await apiRequest<ListServersResponseDto>(LIST_SERVERS_PATH);
  return mapServersSnapshot(data);
}
