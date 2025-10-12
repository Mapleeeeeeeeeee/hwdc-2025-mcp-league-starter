/**
 * Tests for API client timeout functionality.
 *
 * This test suite validates that the API client properly handles request timeouts
 * for long-running operations such as MCP peer-to-peer communication.
 */

import { describe, it, expect, beforeEach, afterEach, vi } from "vitest";
import { apiClient, apiRequest } from "./api-client";
import { ApiError } from "./api-error";

describe("API Client Timeout", () => {
  beforeEach(() => {
    // Mock fetch globally
    global.fetch = vi.fn();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("should_apply_default_timeout_of_120_seconds", async () => {
    // Arrange
    const mockResponse = {
      ok: true,
      json: async () => ({ success: true, data: { result: "ok" } }),
    };
    (global.fetch as ReturnType<typeof vi.fn>).mockResolvedValue(mockResponse);

    // Act
    await apiRequest("/test");

    // Assert
    expect(global.fetch).toHaveBeenCalledWith(
      expect.any(String),
      expect.objectContaining({
        signal: expect.any(AbortSignal),
      }),
    );
  });

  it(
    "should_timeout_after_specified_duration",
    async () => {
      // Arrange
      const mockFetch = vi.fn(
        (_url, options) =>
          new Promise((resolve, reject) => {
            // Listen for abort signal
            if (options?.signal) {
              options.signal.addEventListener("abort", () => {
                const error = new Error("The operation was aborted");
                error.name = "AbortError";
                reject(error);
              });
            }
            // Never resolve - will timeout
            setTimeout(resolve, 10000);
          }),
      );
      global.fetch = mockFetch as unknown as typeof fetch;

      // Act & Assert
      await expect(
        apiRequest("/test", { timeout: 100 }),
      ).rejects.toThrowError();
    },
    { timeout: 10000 },
  );

  it(
    "should_throw_api_error_with_408_status_on_timeout",
    async () => {
      // Arrange
      const mockFetch = vi.fn(
        (_url, options) =>
          new Promise((resolve, reject) => {
            if (options?.signal) {
              options.signal.addEventListener("abort", () => {
                const error = new Error("The operation was aborted");
                error.name = "AbortError";
                reject(error);
              });
            }
            setTimeout(resolve, 10000);
          }),
      );
      global.fetch = mockFetch as unknown as typeof fetch;

      // Act
      try {
        await apiRequest("/test", { timeout: 100 });
        expect.fail("Should have thrown ApiError");
      } catch (error) {
        // Assert
        expect(error).toBeInstanceOf(ApiError);
        expect((error as ApiError).status).toBe(408);
        expect((error as ApiError).type).toBe("RequestTimeout");
      }
    },
    { timeout: 10000 },
  );

  it(
    "should_include_timeout_duration_in_error_message",
    async () => {
      // Arrange
      const mockFetch = vi.fn(
        (_url, options) =>
          new Promise((resolve, reject) => {
            if (options?.signal) {
              options.signal.addEventListener("abort", () => {
                const error = new Error("The operation was aborted");
                error.name = "AbortError";
                reject(error);
              });
            }
            setTimeout(resolve, 10000);
          }),
      );
      global.fetch = mockFetch as unknown as typeof fetch;

      // Act
      try {
        await apiRequest("/test", { timeout: 150 });
        expect.fail("Should have thrown ApiError");
      } catch (error) {
        // Assert
        expect((error as ApiError).message).toContain("150ms");
      }
    },
    { timeout: 10000 },
  );

  it("should_allow_custom_timeout_for_long_operations", async () => {
    // Arrange
    const mockResponse = {
      ok: true,
      json: async () => ({ success: true, data: { result: "ok" } }),
    };

    const mockFetch = vi.fn(async () => {
      // Simulate slow operation
      await new Promise((resolve) => setTimeout(resolve, 200));
      return mockResponse;
    });
    global.fetch = mockFetch as unknown as typeof fetch;

    // Act - Should NOT timeout with 300ms timeout
    const result = await apiRequest<{ result: string }>("/test", {
      timeout: 300,
    });

    // Assert
    expect(result).toEqual({ result: "ok" });
  });

  it("should_clear_timeout_after_successful_request", async () => {
    // Arrange
    const clearTimeoutSpy = vi.spyOn(global, "clearTimeout");
    const mockResponse = {
      ok: true,
      json: async () => ({ success: true, data: { result: "ok" } }),
    };
    (global.fetch as ReturnType<typeof vi.fn>).mockResolvedValue(mockResponse);

    // Act
    await apiRequest("/test");

    // Assert
    expect(clearTimeoutSpy).toHaveBeenCalled();
  });

  it("should_merge_caller_signal_with_timeout_signal", async () => {
    // Arrange
    const controller = new AbortController();
    const mockResponse = {
      ok: true,
      json: async () => ({ success: true, data: { result: "ok" } }),
    };
    (global.fetch as ReturnType<typeof vi.fn>).mockResolvedValue(mockResponse);

    // Act
    await apiRequest("/test", { signal: controller.signal });

    // Assert
    expect(global.fetch).toHaveBeenCalledWith(
      expect.any(String),
      expect.objectContaining({
        signal: expect.any(AbortSignal),
      }),
    );
  });

  it(
    "should_abort_when_caller_aborts_signal",
    async () => {
      // Arrange
      const controller = new AbortController();
      const mockFetch = vi.fn(
        (_url, options) =>
          new Promise((resolve, reject) => {
            if (options?.signal) {
              options.signal.addEventListener("abort", () => {
                const error = new Error("The operation was aborted");
                error.name = "AbortError";
                reject(error);
              });
            }
            setTimeout(resolve, 10000);
          }),
      );
      global.fetch = mockFetch as unknown as typeof fetch;

      // Act
      const requestPromise = apiRequest("/test", { signal: controller.signal });
      controller.abort(); // Abort immediately

      // Assert
      await expect(requestPromise).rejects.toThrow();
    },
    { timeout: 10000 },
  );
});

describe("API Client convenience methods", () => {
  beforeEach(() => {
    global.fetch = vi.fn();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("should_support_timeout_in_post_method", async () => {
    // Arrange
    const mockResponse = {
      ok: true,
      json: async () => ({ success: true, data: { id: 1 } }),
    };
    (global.fetch as ReturnType<typeof vi.fn>).mockResolvedValue(mockResponse);

    // Act
    await apiClient.post("/test", { foo: "bar" }, { timeout: 5000 });

    // Assert
    expect(global.fetch).toHaveBeenCalledWith(
      expect.any(String),
      expect.objectContaining({
        method: "POST",
        signal: expect.any(AbortSignal),
      }),
    );
  });

  it("should_support_timeout_in_get_method", async () => {
    // Arrange
    const mockResponse = {
      ok: true,
      json: async () => ({ success: true, data: { id: 1 } }),
    };
    (global.fetch as ReturnType<typeof vi.fn>).mockResolvedValue(mockResponse);

    // Act
    await apiClient.get("/test", { timeout: 5000 });

    // Assert
    expect(global.fetch).toHaveBeenCalledWith(
      expect.any(String),
      expect.objectContaining({
        method: "GET",
        signal: expect.any(AbortSignal),
      }),
    );
  });
});
