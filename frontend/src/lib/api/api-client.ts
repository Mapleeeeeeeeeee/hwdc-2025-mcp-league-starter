import { ApiError } from "./api-error";
import type { ApiResponse } from "./types";
import { config } from "../config";

type RequestOptions = RequestInit & {
  parseJson?: boolean;
  /**
   * Request timeout in milliseconds.
   * @default 120000 (120 seconds)
   *
   * This timeout is particularly important for long-running operations
   * such as MCP peer-to-peer communication where processing time can exceed
   * browser defaults (typically 60s).
   */
  timeout?: number;
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
  { parseJson = true, timeout = 120000, signal, ...init }: RequestOptions = {},
): Promise<T> {
  const url = buildUrl(path);

  // Create AbortController for timeout
  const controller = new AbortController();
  const timeoutId = setTimeout(() => {
    controller.abort();
  }, timeout);

  // Merge caller's signal with timeout signal
  const mergedSignal = signal
    ? createMergedSignal(signal, controller.signal)
    : controller.signal;

  try {
    const response = await fetch(url, {
      cache: "no-store",
      credentials: "include",
      headers: {
        "Content-Type": "application/json",
        Accept: "application/json",
        ...(init?.headers ?? {}),
      },
      signal: mergedSignal,
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
  } catch (error) {
    // Enhance AbortError with timeout information
    if (error instanceof Error && error.name === "AbortError") {
      throw new ApiError(
        408,
        "RequestTimeout",
        undefined,
        `Request timed out after ${timeout}ms. This may occur during long-running operations.`,
      );
    }
    throw error;
  } finally {
    clearTimeout(timeoutId);
  }
}

/**
 * Creates a merged AbortSignal that aborts when either signal aborts.
 * Returns the timeout signal if caller signal is already aborted.
 */
function createMergedSignal(
  callerSignal: AbortSignal,
  timeoutSignal: AbortSignal,
): AbortSignal {
  // If caller already aborted, return timeout signal
  if (callerSignal.aborted) {
    return callerSignal;
  }

  // Create new controller that listens to both signals
  const mergedController = new AbortController();

  const abortHandler = () => {
    mergedController.abort();
  };

  callerSignal.addEventListener("abort", abortHandler, { once: true });
  timeoutSignal.addEventListener("abort", abortHandler, { once: true });

  return mergedController.signal;
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
