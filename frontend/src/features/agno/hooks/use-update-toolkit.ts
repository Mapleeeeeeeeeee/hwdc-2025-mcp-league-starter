import { useApiMutation } from "@/lib/hooks/use-api-mutation";
import { useQueryClient } from "@tanstack/react-query";

import { updateToolkitEnabled } from "../services";
import type { UpdateToolkitEnabledInput } from "../types";

/**
 * Hook to update toolkit enabled status
 */
export function useUpdateToolkit() {
  const queryClient = useQueryClient();

  return useApiMutation<void, UpdateToolkitEnabledInput>({
    mutationFn: updateToolkitEnabled,
    onSuccess: () => {
      // Invalidate agno config query to refetch
      queryClient.invalidateQueries({ queryKey: ["agno", "config"] });
    },
  });
}
