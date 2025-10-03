/**
 * API Path Constants
 *
 * Centralized management of all API endpoint paths.
 * Ensures consistency between frontend and backend API paths.
 */

export const API_PATHS = {
  // Conversation endpoints
  CONVERSATION: {
    BASE: "/api/v1/conversation",
    STREAM: "/api/v1/conversation/stream",
    MODELS: "/api/v1/conversation/models",
    MODEL_BY_KEY: (key: string) => `/api/v1/conversation/models/${key}`,
  },
  // MCP endpoints
  MCP: {
    SERVERS: "/api/v1/mcp/servers",
    RELOAD_ALL_SERVERS: "/api/v1/mcp/servers:reload",
    RELOAD_SERVER: (serverName: string) =>
      `/api/v1/mcp/servers/${serverName}:reload`,
  },
} as const;

/**
 * API Version constant
 * Used for versioning and future API evolution
 */
export const API_VERSION = "v1";

/**
 * Base API path prefix
 */
export const API_BASE_PATH = `/api/${API_VERSION}`;
