import { apiClient } from "@/lib/api/api-client";
import { API_PATHS } from "@/lib/api/paths";
import { ApiError } from "@/lib/api/api-error";
import { config } from "@/lib/config";
import { fetchEventSource } from "@microsoft/fetch-event-source";

import type {
  ConversationReply,
  ConversationRequestInput,
  ConversationStreamChunk,
  ListModelsResponse,
} from "../types";

type StreamEventHandlers = {
  onChunk?: (chunk: ConversationStreamChunk) => void;
  onError?: (error: ApiError) => void;
  onComplete?: () => void;
};

function buildAbsoluteUrl(path: string): string {
  if (!path.startsWith("/")) {
    return `/${path}`;
  }
  return path;
}

export async function sendConversationRequest(
  payload: ConversationRequestInput,
): Promise<ConversationReply> {
  return apiClient.post<ConversationReply>(
    API_PATHS.CONVERSATION.BASE,
    payload,
    { isLongRunning: true }, // Use long-running timeout
  );
}

export async function fetchConversationModels(): Promise<ListModelsResponse> {
  return apiClient.get<ListModelsResponse>(API_PATHS.CONVERSATION.MODELS);
}

export async function setActiveModel(modelKey: string): Promise<void> {
  return apiClient.put<void>(API_PATHS.CONVERSATION.MODEL_BY_KEY(modelKey));
}

export function streamConversationRequest(
  payload: ConversationRequestInput,
  handlers: StreamEventHandlers = {},
): AbortController {
  const controller = new AbortController();

  const url = buildAbsoluteUrl(API_PATHS.CONVERSATION.STREAM);

  fetchEventSource(url, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Accept: "text/event-stream",
    },
    body: JSON.stringify(payload),
    credentials: "include",
    signal: controller.signal,
    openWhenHidden: true,
    onmessage(event) {
      // event.data is already the parsed data (without "data:" prefix)
      // event.event contains the event type (if any)

      // Skip empty messages
      if (!event.data || event.data.trim() === "") {
        return;
      }

      if (event.event === "error") {
        const errorData = safeParseError(event.data);
        // Convert streaming error to ApiError for consistent error handling
        const apiError = new ApiError(
          500, // Streaming errors are considered server errors
          errorData.type || "StreamingError",
          undefined, // No trace_id in streaming errors
          errorData.message || "Streaming error occurred",
          errorData.i18n_key,
          errorData.i18n_params,
        );
        handlers.onError?.(apiError);
        return;
      }

      try {
        const chunk = JSON.parse(event.data) as ConversationStreamChunk;
        handlers.onChunk?.(chunk);
      } catch (error) {
        // Log parsing errors in development for debugging
        if (config.isDevelopment) {
          console.warn("[Streaming] Failed to parse chunk:", {
            data: event.data,
            error: error instanceof Error ? error.message : String(error),
          });
        }
        // Don't throw error for parsing failures - might be heartbeat or other non-JSON data
        // The stream will continue with next chunk
      }
    },
    async onopen(response) {
      if (response.ok) {
        // Connection opened successfully
      } else {
        const apiError = new ApiError(
          response.status,
          "StreamConnectionError",
          undefined,
          `Streaming request failed with status ${response.status}`,
        );
        handlers.onError?.(apiError);
      }
    },
    onerror(error) {
      if (!controller.signal.aborted) {
        const apiError =
          error instanceof ApiError
            ? error
            : new ApiError(
                500,
                "StreamNetworkError",
                undefined,
                error instanceof Error ? error.message : String(error),
              );
        handlers.onError?.(apiError);
      }
    },
    onclose() {
      if (!controller.signal.aborted) {
        handlers.onComplete?.();
      }
    },
  });

  return controller;
}

type StreamErrorData = {
  type?: string;
  message?: string;
  context?: Record<string, unknown>;
  i18n_key?: string;
  i18n_params?: Record<string, string | number>;
};

function safeParseError(payload: string): StreamErrorData {
  try {
    const parsed = JSON.parse(payload) as StreamErrorData;
    return parsed;
  } catch {
    return {
      type: "ParseError",
      message: payload || "Streaming error",
    };
  }
}
