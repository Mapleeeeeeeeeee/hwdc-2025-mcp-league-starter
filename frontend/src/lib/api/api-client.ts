import { ApiError } from "./api-error";
import type { ApiResponse } from "./types";
import { config } from "../config";

type RequestOptions = RequestInit & {
  parseJson?: boolean;
};

/**
 * Ensures path is a valid relative URL starting with /
 * API routing is handled by:
 * - Development: Next.js rewrites (next.config.ts)
 * - Production: Nginx reverse proxy
 */
function buildUrl(path: string): string {
  if (!path.startsWith("/")) {
    if (config.isDevelopment) {
      console.warn(`API path should start with /: ${path}`);
    }
    return `/${path}`;
  }
  return path;
}

export async function apiRequest<T>(
  path: string,
  { parseJson = true, ...init }: RequestOptions = {},
): Promise<T> {
  const url = buildUrl(path);
  const response = await fetch(url, {
    cache: "no-store",
    credentials: "include",
    headers: {
      "Content-Type": "application/json",
      Accept: "application/json",
      ...(init?.headers ?? {}),
    },
    ...init,
  });

  if (!parseJson) {
    return response as unknown as T;
  }

  let payload: ApiResponse<T> | null = null;

  try {
    payload = (await response.json()) as ApiResponse<T>;
  } catch (error) {
    if (config.isDevelopment) {
      console.error("Failed to parse API response", { url, error });
    }
    throw new ApiError(
      response.status,
      "InvalidJsonResponse",
      undefined,
      undefined,
    );
  }

  if (!response.ok || !payload?.success) {
    if (payload && "success" in payload && !payload.success) {
      throw ApiError.fromPayload(response.status, payload);
    }

    throw new ApiError(
      response.status,
      "UnknownApiError",
      payload?.trace_id,
      payload && "message" in payload ? payload.message : undefined,
    );
  }

  return payload.data;
}

// Convenience methods for better developer experience
export const apiClient = {
  get: <T>(
    path: string,
    options?: Omit<RequestOptions, "method" | "body">,
  ): Promise<T> => apiRequest<T>(path, { ...options, method: "GET" }),

  post: <T, B = unknown>(
    path: string,
    body?: B,
    options?: Omit<RequestOptions, "method" | "body">,
  ): Promise<T> =>
    apiRequest<T>(path, {
      ...options,
      method: "POST",
      body: body ? JSON.stringify(body) : undefined,
    }),

  put: <T, B = unknown>(
    path: string,
    body?: B,
    options?: Omit<RequestOptions, "method" | "body">,
  ): Promise<T> =>
    apiRequest<T>(path, {
      ...options,
      method: "PUT",
      body: body ? JSON.stringify(body) : undefined,
    }),

  patch: <T, B = unknown>(
    path: string,
    body?: B,
    options?: Omit<RequestOptions, "method" | "body">,
  ): Promise<T> =>
    apiRequest<T>(path, {
      ...options,
      method: "PATCH",
      body: body ? JSON.stringify(body) : undefined,
    }),

  delete: <T>(
    path: string,
    options?: Omit<RequestOptions, "method" | "body">,
  ): Promise<T> => apiRequest<T>(path, { ...options, method: "DELETE" }),
};
