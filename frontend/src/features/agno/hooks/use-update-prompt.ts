import { useApiMutation } from "@/lib/hooks/use-api-mutation";
import { useQueryClient } from "@tanstack/react-query";

import { updatePromptEnabled } from "../services";
import type { UpdatePromptEnabledInput } from "../types";

/**
 * Hook to update prompt enabled status
 */
export function useUpdatePrompt() {
  const queryClient = useQueryClient();

  return useApiMutation<void, UpdatePromptEnabledInput>({
    mutationFn: updatePromptEnabled,
    onSuccess: () => {
      // Invalidate agno config query to refetch
      queryClient.invalidateQueries({ queryKey: ["agno", "config"] });
    },
  });
}
