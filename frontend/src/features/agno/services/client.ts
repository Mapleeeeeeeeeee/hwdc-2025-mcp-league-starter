import { apiClient } from "@/lib/api/api-client";

import type {
  AgnoConfiguration,
  UpdatePromptEnabledInput,
  UpdateToolkitEnabledInput,
} from "../types";

const AGNO_BASE_PATH = "/api/v1/agno";

export async function fetchAgnoConfig(): Promise<AgnoConfiguration> {
  return apiClient.get<AgnoConfiguration>(`${AGNO_BASE_PATH}/config`);
}

export async function updateToolkitEnabled(
  input: UpdateToolkitEnabledInput,
): Promise<void> {
  return apiClient.patch<void>(`${AGNO_BASE_PATH}/toolkits/${input.key}`, {
    enabled: input.enabled,
  });
}

export async function updatePromptEnabled(
  input: UpdatePromptEnabledInput,
): Promise<void> {
  return apiClient.patch<void>(`${AGNO_BASE_PATH}/prompts/${input.key}`, {
    enabled: input.enabled,
  });
}
