"use client";

import type { ConversationReply, ConversationRequestInput } from "../types";
import { sendConversationRequest } from "../services";

import { useApiMutation } from "@/lib/hooks";

export function useConversationMutation() {
  return useApiMutation<ConversationReply, ConversationRequestInput>({
    mutationFn: sendConversationRequest,
  });
}
