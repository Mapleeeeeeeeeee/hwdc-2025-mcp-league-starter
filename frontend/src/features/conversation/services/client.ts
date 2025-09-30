import { apiClient } from "@/lib/api/api-client";
import { API_PATHS } from "@/lib/api/paths";

import type { ConversationReply, ConversationRequestInput } from "../types";

export async function sendConversationRequest(
  payload: ConversationRequestInput,
): Promise<ConversationReply> {
  return apiClient.post<ConversationReply>(
    API_PATHS.CONVERSATION.BASE,
    payload,
  );
}
