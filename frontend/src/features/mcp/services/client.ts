import { apiClient } from "@/lib/api/api-client";
import { API_PATHS } from "@/lib/api/paths";

import type { McpServersSnapshot } from "../types";

export async function listServers(): Promise<McpServersSnapshot> {
  return apiClient.get<McpServersSnapshot>(API_PATHS.MCP.SERVERS);
}
