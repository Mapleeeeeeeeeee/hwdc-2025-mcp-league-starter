import { ApiError } from "./api-error";
import type { ApiResponse } from "./types";

const DEFAULT_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

type RequestOptions = RequestInit & {
  baseUrl?: string;
  parseJson?: boolean;
};

function buildUrl(path: string, baseUrl: string) {
  try {
    return new URL(path, baseUrl).toString();
  } catch (error) {
    if (process.env.NODE_ENV !== "production") {
      console.error("Failed to build API URL", { path, baseUrl, error });
    }
    throw error;
  }
}

export async function apiRequest<T>(
  path: string,
  { baseUrl = DEFAULT_BASE_URL, parseJson = true, ...init }: RequestOptions = {},
): Promise<T> {
  const url = buildUrl(path, baseUrl);
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
    if (process.env.NODE_ENV !== "production") {
      console.error("Failed to parse API response", { url, error });
    }
    throw new ApiError(response.status, "InvalidJsonResponse", undefined, undefined);
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
