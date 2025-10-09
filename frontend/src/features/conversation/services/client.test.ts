import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import {
  streamConversationRequest,
  sendConversationRequest,
  fetchConversationModels,
} from "./client";
import type { ConversationRequestInput } from "../types";
import { apiClient } from "@/lib/api/api-client";
import { fetchEventSource } from "@microsoft/fetch-event-source";

// Mock dependencies
vi.mock("@/lib/api/api-client");
vi.mock("@microsoft/fetch-event-source", () => ({
  fetchEventSource: vi.fn(),
}));

const mockApiClient = vi.mocked(apiClient);
const mockFetchEventSource = vi.mocked(fetchEventSource);

describe("Conversation Client", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  describe("sendConversationRequest", () => {
    it("should_return_response_when_apiClient_post_succeeds", async () => {
      const payload: ConversationRequestInput = {
        conversationId: "conv-1",
        history: [{ role: "user", content: "test" }],
        modelKey: "gpt-4",
      };
      const expectedResponse = { reply: "response" };

      mockApiClient.post.mockResolvedValue(expectedResponse);

      const result = await sendConversationRequest(payload);

      expect(mockApiClient.post).toHaveBeenCalledWith(
        "/api/v1/conversation",
        payload,
      );
      expect(result).toEqual(expectedResponse);
    });
  });

  describe("fetchConversationModels", () => {
    it("should_return_models_when_apiClient_get_succeeds", async () => {
      const expectedResponse = { models: ["gpt-4", "gpt-3.5"] };

      mockApiClient.get.mockResolvedValue(expectedResponse);

      const result = await fetchConversationModels();

      expect(mockApiClient.get).toHaveBeenCalledWith(
        "/api/v1/conversation/models",
      );
      expect(result).toEqual(expectedResponse);
    });
  });

  describe("streamConversationRequest", () => {
    beforeEach(() => {
      vi.clearAllMocks();
    });

    it("should_call_fetchEventSource_with_correct_config_when_stream_starts", async () => {
      const payload: ConversationRequestInput = {
        conversationId: "conv-1",
        history: [{ role: "user", content: "test" }],
        modelKey: "gpt-4",
      };

      mockFetchEventSource.mockImplementation(() => Promise.resolve());

      const controller = streamConversationRequest(payload, {});

      expect(mockFetchEventSource).toHaveBeenCalledWith(
        "/api/v1/conversation/stream",
        expect.objectContaining({
          method: "POST",
          headers: expect.objectContaining({
            "Content-Type": "application/json",
          }),
          body: JSON.stringify(payload),
          signal: controller.signal,
        }),
      );

      expect(controller).toBeInstanceOf(AbortController);
    });

    it("should_invoke_onChunk_callback_when_message_received", async () => {
      const payload: ConversationRequestInput = {
        conversationId: "conv-1",
        history: [{ role: "user", content: "test" }],
      };
      const onChunk = vi.fn();
      const handlers = { onChunk };

      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      mockFetchEventSource.mockImplementation((_url: any, options: any) => {
        // Simulate onmessage callback with SSE-formatted data
        if (options.onmessage) {
          options.onmessage({
            data: 'data: {"delta": "test chunk"}',
            event: "",
            id: "",
          });
        }
        return Promise.resolve();
      });

      streamConversationRequest(payload, handlers);

      await vi.waitFor(() => {
        expect(onChunk).toHaveBeenCalledWith({ delta: "test chunk" });
      });
    });

    it("should_invoke_onError_callback_when_error_occurs", async () => {
      const payload: ConversationRequestInput = {
        conversationId: "conv-1",
        history: [{ role: "user", content: "test" }],
      };
      const onError = vi.fn();
      const handlers = { onError };

      const testError = new Error("test error");
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      mockFetchEventSource.mockImplementation((_url: any, options: any) => {
        // Simulate onerror callback
        if (options.onerror) {
          options.onerror(testError);
        }
        return Promise.resolve();
      });

      streamConversationRequest(payload, handlers);

      await vi.waitFor(() => {
        expect(onError).toHaveBeenCalledWith(testError);
      });
    });

    it("should_invoke_onComplete_callback_when_stream_closes", async () => {
      const payload: ConversationRequestInput = {
        conversationId: "conv-1",
        history: [{ role: "user", content: "test" }],
      };
      const onComplete = vi.fn();
      const handlers = { onComplete };

      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      mockFetchEventSource.mockImplementation((_url: any, options: any) => {
        // Simulate onclose callback
        if (options.onclose) {
          options.onclose();
        }
        return Promise.resolve();
      });

      streamConversationRequest(payload, handlers);

      await vi.waitFor(() => {
        expect(onComplete).toHaveBeenCalled();
      });
    });

    it("should_abort_stream_when_controller_aborted", async () => {
      const payload: ConversationRequestInput = {
        conversationId: "conv-1",
        history: [{ role: "user", content: "test" }],
      };
      const onComplete = vi.fn();
      const handlers = { onComplete };

      mockFetchEventSource.mockImplementation(() => Promise.resolve());

      const controller = streamConversationRequest(payload, handlers);

      controller.abort();

      expect(controller.signal.aborted).toBe(true);
    });
  });
});
