import type { McpToolSelection } from "@/features/mcp";

export type ConversationRole = "user" | "assistant" | "system";

export type ConversationMessage = {
  role: ConversationRole;
  content: string;
};

export type ConversationHistory = ConversationMessage[];

export type ConversationRequestInput = {
  conversationId: string;
  history: ConversationHistory;
  userId?: string;
  modelKey?: string;
  tools?: McpToolSelection[];
};

export type ConversationReply = {
  conversationId: string;
  messageId: string;
  content: string;
  modelKey: string;
};
