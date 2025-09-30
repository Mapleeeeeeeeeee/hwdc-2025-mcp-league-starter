"use client";

import { useMemo } from "react";

import { useApi } from "@/lib/hooks";

import { fetchConversationModels } from "../services";
import type { ListModelsResponse, LLMModelDescriptor } from "../types";

export type UseConversationModelsResult = {
  activeModelKey?: string;
  models: LLMModelDescriptor[];
};

export function useConversationModels() {
  const query = useApi<ListModelsResponse>({
    queryKey: ["conversation", "models"],
    queryFn: fetchConversationModels,
    staleTime: 60_000,
  });

  const data = useMemo<UseConversationModelsResult>(() => {
    if (!query.data) {
      return { models: [] };
    }

    return {
      activeModelKey: query.data.activeModelKey,
      models: query.data.models,
    };
  }, [query.data]);

  return {
    ...query,
    data,
  };
}
