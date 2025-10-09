import { apiClient } from "@/lib/api/api-client";
import { API_PATHS } from "@/lib/api/paths";
import { fetchEventSource } from "@microsoft/fetch-event-source";

import type {
  ConversationReply,
  ConversationRequestInput,
  ConversationStreamChunk,
  ListModelsResponse,
} from "../types";

type StreamEventHandlers = {
  onChunk?: (chunk: ConversationStreamChunk) => void;
  onError?: (error: Error) => void;
  onComplete?: () => void;
};

const SSE_EVENT_PREFIX = "event:";
const SSE_DATA_PREFIX = "data:";

/**
 * Build URL for SSE endpoint
 * Uses relative path - routing handled by Next.js rewrites (dev) or Nginx (prod)
 */
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
    onmessage(event) {
      handleEvent(event.data, handlers);
    },
    async onopen(response) {
      if (response.ok) {
        // Connection opened successfully
      } else {
        handlers.onError?.(
          new Error(`Streaming request failed with status ${response.status}`),
        );
      }
    },
    onerror(error) {
      if (!controller.signal.aborted) {
        handlers.onError?.(
          error instanceof Error ? error : new Error(String(error)),
        );
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

function handleEvent(eventPayload: string, handlers: StreamEventHandlers) {
  const lines = eventPayload
    .split(/\r?\n/)
    .map((line) => line.trim())
    .filter(Boolean);

  if (lines.length === 0) {
    return;
  }

  let eventType = "message";
  const dataLines: string[] = [];

  for (const line of lines) {
    if (line.startsWith(SSE_EVENT_PREFIX)) {
      eventType = line.slice(SSE_EVENT_PREFIX.length).trim();
    } else if (line.startsWith(SSE_DATA_PREFIX)) {
      dataLines.push(line.slice(SSE_DATA_PREFIX.length).trim());
    }
  }

  if (dataLines.length === 0) {
    return;
  }

  const payloadRaw = dataLines.join("\n");

  if (eventType === "error") {
    const errorMessage = safeParseError(payloadRaw);
    handlers.onError?.(new Error(errorMessage));
    return;
  }

  try {
    const chunk = JSON.parse(payloadRaw) as ConversationStreamChunk;
    handlers.onChunk?.(chunk);
  } catch (error) {
    handlers.onError?.(
      error instanceof Error ? error : new Error(String(error)),
    );
  }
}

function safeParseError(payload: string): string {
  try {
    const parsed = JSON.parse(payload) as { message?: string };
    return parsed.message ?? "Streaming error";
  } catch {
    return payload || "Streaming error";
  }
}
