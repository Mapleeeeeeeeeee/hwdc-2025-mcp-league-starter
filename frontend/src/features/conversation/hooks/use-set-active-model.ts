"use client";

import { useMutation, useQueryClient } from "@tanstack/react-query";

import { setActiveModel } from "../services";
import type { ListModelsResponse } from "../types";

export function useSetActiveModel() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (modelKey: string) => setActiveModel(modelKey),
    onSuccess: (_data, modelKey) => {
      // Update the active model in the cache
      queryClient.setQueryData<ListModelsResponse>(
        ["conversation", "models"],
        (oldData) => {
          if (!oldData) return oldData;
          return {
            ...oldData,
            activeModelKey: modelKey,
          };
        },
      );
    },
  });
}
