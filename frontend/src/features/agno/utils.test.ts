import { describe, expect, it } from "vitest";

import { enhanceMessageWithToolHints } from "./utils";

describe("enhanceMessageWithToolHints", () => {
  it("should return original message when no tools selected", () => {
    const message = "What is the weather today?";
    const result = enhanceMessageWithToolHints(message, []);

    expect(result).toBe(message);
  });

  it("should add single tool hint to message", () => {
    const message = "Search for SpaceX news";
    const result = enhanceMessageWithToolHints(message, ["duckduckgo_search"]);

    expect(result).toBe(
      "Search for SpaceX news\n\nPlease use duckduckgo search to help answer this question.",
    );
  });

  it("should add multiple tools hint to message", () => {
    const message = "Analyze this code";
    const result = enhanceMessageWithToolHints(message, [
      "python_code_runner",
      "code_analyzer",
    ]);

    expect(result).toBe(
      "Analyze this code\n\nPlease use python code runner, code analyzer to help answer this question.",
    );
  });

  it("should replace underscores with spaces in tool names", () => {
    const message = "Help me";
    const result = enhanceMessageWithToolHints(message, [
      "some_complex_tool_name",
    ]);

    expect(result).toContain("some complex tool name");
  });
});
