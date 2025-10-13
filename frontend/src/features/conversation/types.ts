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
  promptKey?: string;
  tools?: McpToolSelection[];
};

export type ConversationReply = {
  conversationId: string;
  messageId: string;
  content: string;
  modelKey: string;
};

export type ConversationStreamChunk = {
  conversationId: string;
  messageId: string;
  delta: string;
  modelKey: string;
};

export type LLMModelDescriptor = {
  key: string;
  provider: string;
  modelId: string;
  supportsStreaming: boolean;
  metadata?: Record<string, string | number | boolean | null>;
  baseUrl?: string | null;
};

export type ListModelsResponse = {
  activeModelKey: string;
  models: LLMModelDescriptor[];
};
