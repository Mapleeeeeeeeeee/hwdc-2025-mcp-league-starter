import { apiClient } from "@/lib/api/api-client";
import { API_PATHS } from "@/lib/api/paths";

import type {
  McpServersSnapshot,
  ReloadAllMcpServersResponse,
  ReloadMcpServerResponse,
} from "../types";

export async function listServers(): Promise<McpServersSnapshot> {
  return apiClient.get<McpServersSnapshot>(API_PATHS.MCP.SERVERS);
}

export async function reloadAllServers(): Promise<ReloadAllMcpServersResponse> {
  return apiClient.post<ReloadAllMcpServersResponse>(
    API_PATHS.MCP.RELOAD_ALL_SERVERS,
  );
}

export async function reloadServer(
  serverName: string,
): Promise<ReloadMcpServerResponse> {
  return apiClient.post<ReloadMcpServerResponse>(
    API_PATHS.MCP.RELOAD_SERVER(serverName),
  );
}
