import { apiClient } from "@/lib/api/api-client";
import { API_PATHS } from "@/lib/api/paths";
import { config } from "@/lib/config";

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

function buildAbsoluteUrl(path: string) {
  return new URL(path, config.apiBaseUrl).toString();
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

export function streamConversationRequest(
  payload: ConversationRequestInput,
  handlers: StreamEventHandlers = {},
): AbortController {
  const controller = new AbortController();

  const processStream = async () => {
    try {
      const response = await fetch(
        buildAbsoluteUrl(API_PATHS.CONVERSATION.STREAM),
        {
          method: "POST",
          credentials: "include",
          cache: "no-store",
          headers: {
            "Content-Type": "application/json",
            Accept: "text/event-stream",
          },
          body: JSON.stringify(payload),
          signal: controller.signal,
        },
      );

      if (!response.ok || !response.body) {
        throw new Error(
          `Streaming request failed with status ${response.status}`,
        );
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder("utf-8");
      let buffer = "";

      while (true) {
        const { value, done } = await reader.read();
        if (done) {
          break;
        }

        buffer += decoder.decode(value, { stream: true });

        let separatorIndex = buffer.indexOf("\n\n");
        while (separatorIndex !== -1) {
          const rawEvent = buffer.slice(0, separatorIndex);
          buffer = buffer.slice(separatorIndex + 2);
          handleEvent(rawEvent, handlers);
          separatorIndex = buffer.indexOf("\n\n");
        }
      }

      // flush any remaining event (no trailing newline)
      if (buffer.trim().length > 0) {
        handleEvent(buffer, handlers);
      }

      if (!controller.signal.aborted) {
        handlers.onComplete?.();
      }
    } catch (error) {
      if (controller.signal.aborted) {
        return;
      }
      handlers.onError?.(
        error instanceof Error ? error : new Error(String(error)),
      );
    }
  };

  void processStream();

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
    if (line.startsWith("event:")) {
      eventType = line.slice("event:".length).trim();
    } else if (line.startsWith("data:")) {
      dataLines.push(line.slice("data:".length).trim());
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
