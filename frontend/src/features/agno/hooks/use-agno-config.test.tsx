import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen, waitFor } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import * as agnoServices from "../services";
import { useAgnoConfig } from "./use-agno-config";

vi.mock("../services", () => ({
  fetchAgnoConfig: vi.fn(),
}));

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

function TestComponent() {
  const { data, isLoading, error } = useAgnoConfig();

  if (isLoading) return <div>Loading...</div>;
  if (error) return <div>Error: {String(error)}</div>;
  if (!data) return <div>No data</div>;

  return (
    <div>
      <div data-testid="toolkit-count">{data.toolkits.length}</div>
      <div data-testid="prompt-count">{data.prompts.length}</div>
    </div>
  );
}

describe("useAgnoConfig", () => {
  it("should fetch and return agno configuration", async () => {
    vi.mocked(agnoServices.fetchAgnoConfig).mockResolvedValue(mockConfig);

    const queryClient = new QueryClient({
      defaultOptions: { queries: { retry: false } },
    });

    render(
      <QueryClientProvider client={queryClient}>
        <TestComponent />
      </QueryClientProvider>,
    );

    expect(screen.getByText("Loading...")).toBeInTheDocument();

    await waitFor(() => {
      expect(screen.getByTestId("toolkit-count")).toHaveTextContent("1");
      expect(screen.getByTestId("prompt-count")).toHaveTextContent("1");
    });
  });

  it("should handle errors", async () => {
    vi.mocked(agnoServices.fetchAgnoConfig).mockRejectedValue(
      new Error("Network error"),
    );

    const queryClient = new QueryClient({
      defaultOptions: { queries: { retry: false } },
    });

    render(
      <QueryClientProvider client={queryClient}>
        <TestComponent />
      </QueryClientProvider>,
    );

    await waitFor(() => {
      expect(screen.getByText(/Error:/)).toBeInTheDocument();
    });
  });
});
