import { useApi } from "@/lib/hooks/use-api";

import { fetchAgnoConfig } from "../services";
import type { AgnoConfiguration } from "../types";

/**
 * Hook to fetch Agno configuration (toolkits and prompts)
 */
export function useAgnoConfig() {
  return useApi<AgnoConfiguration>({
    queryKey: ["agno", "config"],
    queryFn: fetchAgnoConfig,
  });
}
