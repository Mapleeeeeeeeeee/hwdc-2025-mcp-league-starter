"use client";

import { useCallback } from "react";
import { keepPreviousData } from "@tanstack/react-query";

import { useApi } from "@/lib/hooks";

import type { McpServersSnapshot } from "../types";
import { listServers } from "../services";

export type UseFetchMcpServersOptions = {
  initialData?: McpServersSnapshot;
};

export function useFetchMcpServers({
  initialData,
}: UseFetchMcpServersOptions = {}) {
  const query = useApi<McpServersSnapshot>({
    queryKey: ["mcp", "servers"],
    queryFn: listServers,
    placeholderData: keepPreviousData,
    initialData,
    staleTime: initialData ? 10_000 : undefined,
  });

  const refresh = useCallback(async () => {
    const result = await query.refetch({ throwOnError: false });
    return result.data;
  }, [query]);

  return {
    ...query,
    refresh,
  };
}
