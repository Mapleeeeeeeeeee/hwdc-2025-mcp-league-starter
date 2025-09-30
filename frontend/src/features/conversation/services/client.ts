import { apiClient } from "@/lib/api/api-client";

import type { ConversationReply, ConversationRequestInput } from "../types";

const CONVERSATION_PATH = "/api/v1/conversation";

export async function sendConversationRequest(
  payload: ConversationRequestInput,
): Promise<ConversationReply> {
  return apiClient.post<ConversationReply>(CONVERSATION_PATH, payload);
}
