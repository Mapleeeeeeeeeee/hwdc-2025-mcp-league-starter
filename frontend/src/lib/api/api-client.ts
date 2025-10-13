import { ApiError } from "./api-error";
import type { ApiResponse } from "./types";
import { config } from "../config";

type RequestOptions = RequestInit & {
  parseJson?: boolean;
  timeout?: number;
  isLongRunning?: boolean;
};

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
  {
    parseJson = true,
    timeout,
    isLongRunning = false,
    signal,
    ...init
  }: RequestOptions = {},
): Promise<T> {
  const url = buildUrl(path);

  const resolvedTimeout =
    timeout ??
    (isLongRunning ? config.apiTimeoutLongRunning : config.apiTimeout);

  const controller = new AbortController();
  const timeoutId = setTimeout(() => {
    controller.abort();
  }, resolvedTimeout);

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

    // Handle 204 No Content responses
    if (response.status === 204) {
      return undefined as T;
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
    if (error instanceof Error && error.name === "AbortError") {
      throw new ApiError(
        408,
        "RequestTimeout",
        undefined,
        `Request timed out after ${resolvedTimeout}ms. This may occur during long-running operations.`,
      );
    }
    throw error;
  } finally {
    clearTimeout(timeoutId);
  }
}

function createMergedSignal(
  callerSignal: AbortSignal,
  timeoutSignal: AbortSignal,
): AbortSignal {
  if (callerSignal.aborted) {
    return callerSignal;
  }

  const mergedController = new AbortController();

  const abortHandler = () => {
    mergedController.abort();
  };

  callerSignal.addEventListener("abort", abortHandler, { once: true });
  timeoutSignal.addEventListener("abort", abortHandler, { once: true });

  return mergedController.signal;
}

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
