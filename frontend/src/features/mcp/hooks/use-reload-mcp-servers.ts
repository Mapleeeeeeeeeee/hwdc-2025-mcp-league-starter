"use client";

import { useCallback } from "react";
import { useQueryClient } from "@tanstack/react-query";

import { useApiMutation } from "@/lib/hooks";

import type {
  ReloadAllMcpServersResponse,
  ReloadMcpServerResponse,
} from "../types";
import { reloadAllServers, reloadServer } from "../services";

export function useReloadAllMcpServers() {
  const queryClient = useQueryClient();

  const mutation = useApiMutation<ReloadAllMcpServersResponse>({
    mutationFn: reloadAllServers,
    onSuccess: () => {
      // Invalidate MCP servers query to refresh the list
      void queryClient.invalidateQueries({ queryKey: ["mcp", "servers"] });
    },
  });

  const reload = useCallback(async () => {
    return mutation.mutateAsync();
  }, [mutation]);

  return {
    ...mutation,
    reload,
  };
}

export function useReloadMcpServer() {
  const queryClient = useQueryClient();

  const mutation = useApiMutation<ReloadMcpServerResponse, string>({
    mutationFn: (serverName) => reloadServer(serverName),
    onSuccess: () => {
      // Invalidate MCP servers query to refresh the list
      void queryClient.invalidateQueries({ queryKey: ["mcp", "servers"] });
    },
  });

  const reload = useCallback(
    async (serverName: string) => {
      return mutation.mutateAsync(serverName);
    },
    [mutation],
  );

  return {
    ...mutation,
    reload,
  };
}
