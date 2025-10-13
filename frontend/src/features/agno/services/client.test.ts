import { describe, expect, it, vi } from "vitest";

import { apiClient } from "@/lib/api/api-client";

import {
  fetchAgnoConfig,
  updatePromptEnabled,
  updateToolkitEnabled,
} from "./client";

vi.mock("@/lib/api/api-client", () => ({
  apiClient: {
    get: vi.fn(),
    patch: vi.fn(),
  },
}));

describe("Agno API Client", () => {
  describe("fetchAgnoConfig", () => {
    it("should call GET /api/v1/agno/config", async () => {
      const mockConfig = {
        toolkits: [
          {
            key: "duckduckgo_search",
            toolkitClass: "agno.tools.duckduckgo.DuckDuckGoTools",
            enabled: true,
            config: {},
          },
        ],
        prompts: [
          {
            key: "default",
            name: "Default Instructions",
            enabled: true,
            instructionCount: 3,
          },
        ],
      };

      vi.mocked(apiClient.get).mockResolvedValue(mockConfig);

      const result = await fetchAgnoConfig();

      expect(apiClient.get).toHaveBeenCalledWith("/api/v1/agno/config");
      expect(result).toEqual(mockConfig);
    });
  });

  describe("updateToolkitEnabled", () => {
    it("should call PATCH /api/v1/agno/toolkits/{key}", async () => {
      vi.mocked(apiClient.patch).mockResolvedValue(undefined);

      await updateToolkitEnabled({ key: "duckduckgo_search", enabled: false });

      expect(apiClient.patch).toHaveBeenCalledWith(
        "/api/v1/agno/toolkits/duckduckgo_search",
        { enabled: false },
      );
    });
  });

  describe("updatePromptEnabled", () => {
    it("should call PATCH /api/v1/agno/prompts/{key}", async () => {
      vi.mocked(apiClient.patch).mockResolvedValue(undefined);

      await updatePromptEnabled({ key: "analytical", enabled: true });

      expect(apiClient.patch).toHaveBeenCalledWith(
        "/api/v1/agno/prompts/analytical",
        { enabled: true },
      );
    });
  });
});
