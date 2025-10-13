import { useCallback, useEffect, useRef, useState } from "react";
import { useTranslations } from "next-intl";

import {
  ConversationMessage,
  ConversationReply,
  ConversationRequestInput,
  ConversationStreamChunk,
  streamConversationRequest,
} from "@/features/conversation";
import { useConversationMutation } from "@/features/conversation";
import type { McpToolSelection } from "@/features/mcp";
import { ApiError } from "@/lib/api/api-error";

type ChatMessage = ConversationMessage & {
  id: string;
};

interface UseConversationOptions {
  conversationId: string;
  initialMessages?: ChatMessage[];
  userId?: string;
  modelKey?: string;
  promptKey?: string;
  tools?: McpToolSelection[];
  supportsStreaming?: boolean;
}

interface UseConversationReturn {
  messages: ChatMessage[];
  isStreaming: boolean;
  isStreamingEnabled: boolean;
  isBusy: boolean;
  error: string | null;
  sendMessage: (content: string) => Promise<void>;
  cancelStream: () => void;
  setIsStreamingEnabled: (enabled: boolean) => void;
}

function toHistory(messages: ChatMessage[]): ConversationMessage[] {
  return messages
    .filter(({ content }) => content.trim().length > 0)
    .map(({ role, content }) => ({ role, content }));
}

function getErrorMessage(
  translateChat: (key: string) => string,
  translateErrors: (
    key: string,
    values?: Record<string, string | number | Date>,
  ) => string,
  error: unknown,
): string {
  if (!(error instanceof ApiError)) {
    if (error instanceof Error && error.message) {
      return error.message;
    }
    return translateChat("error.generic");
  }

  const scopedKey = error.i18nKey?.startsWith("errors.")
    ? error.i18nKey.slice("errors.".length)
    : error.i18nKey;

  if (scopedKey) {
    try {
      return translateErrors(scopedKey, error.i18nParams);
    } catch {
      // ignore and fallback
    }
  }

  return translateChat("error.generic");
}

function appendAssistantMessage(
  messages: ChatMessage[],
  reply: ConversationReply,
): ChatMessage[] {
  return [
    ...messages,
    {
      id: reply.messageId,
      role: "assistant",
      content: reply.content,
    },
  ];
}

/**
 * Hook for managing conversation state and streaming
 * Encapsulates all conversation logic: messages, streaming, API calls
 */
export function useConversation({
  conversationId,
  initialMessages = [],
  userId,
  modelKey,
  promptKey,
  tools,
  supportsStreaming = false,
}: UseConversationOptions): UseConversationReturn {
  const tChat = useTranslations("common.chat");
  const tErrors = useTranslations("errors");

  const [messages, setMessages] = useState<ChatMessage[]>(initialMessages);
  const [isStreamingEnabled, setIsStreamingEnabled] = useState(true);
  const [isStreamingActive, setIsStreamingActive] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const streamControllerRef = useRef<AbortController | null>(null);
  const mutation = useConversationMutation();

  const isBusy = mutation.isPending || isStreamingActive;

  // Disable streaming if model doesn't support it
  useEffect(() => {
    if (!supportsStreaming && isStreamingEnabled) {
      setIsStreamingEnabled(false);
    }
  }, [supportsStreaming, isStreamingEnabled]);

  // Cleanup on unmount
  useEffect(
    () => () => {
      streamControllerRef.current?.abort();
    },
    [],
  );

  const cancelStream = useCallback(() => {
    if (streamControllerRef.current) {
      streamControllerRef.current.abort();
      streamControllerRef.current = null;
    }
    setIsStreamingActive(false);
  }, []);

  const sendMessage = useCallback(
    async (content: string) => {
      if (isBusy || !content.trim()) return;

      setError(null);
      cancelStream();

      const userMessage: ChatMessage = {
        id: crypto.randomUUID(),
        role: "user",
        content,
      };

      const nextMessages = [...messages, userMessage];
      const history = toHistory(nextMessages);

      const payload: ConversationRequestInput = {
        conversationId,
        history,
        userId,
        modelKey,
        promptKey,
        tools: tools && tools.length > 0 ? tools : undefined,
      };

      const shouldStream = isStreamingEnabled && supportsStreaming;

      if (shouldStream) {
        const placeholderId = crypto.randomUUID();
        const assistantPlaceholder: ChatMessage = {
          id: placeholderId,
          role: "assistant",
          content: "",
        };

        setMessages([...nextMessages, assistantPlaceholder]);
        setIsStreamingActive(true);

        const handleChunk = (chunk: ConversationStreamChunk) => {
          setMessages((prev) => {
            let found = false;
            const updated = prev.map((message) => {
              if (
                message.id === placeholderId ||
                message.id === chunk.messageId
              ) {
                found = true;
                return {
                  ...message,
                  id: chunk.messageId,
                  content: `${message.content}${chunk.delta}`,
                };
              }
              return message;
            });

            if (!found) {
              return [
                ...updated,
                {
                  id: chunk.messageId,
                  role: "assistant",
                  content: chunk.delta,
                },
              ];
            }

            return updated;
          });
        };

        const handleStreamError = (err: Error) => {
          streamControllerRef.current = null;
          setIsStreamingActive(false);
          setError(err.message || tChat("error.generic"));
          setMessages((prev) =>
            prev.filter((message) => message.id !== placeholderId),
          );
        };

        const handleStreamComplete = () => {
          streamControllerRef.current = null;
          setIsStreamingActive(false);
        };

        streamControllerRef.current = streamConversationRequest(payload, {
          onChunk: handleChunk,
          onError: handleStreamError,
          onComplete: handleStreamComplete,
        });
      } else {
        setMessages(nextMessages);

        try {
          const reply = await mutation.mutateAsync(payload);
          setMessages((prev) => appendAssistantMessage(prev, reply));
        } catch (err) {
          setError(getErrorMessage(tChat, tErrors, err));
        }
      }
    },
    [
      conversationId,
      isBusy,
      isStreamingEnabled,
      messages,
      mutation,
      cancelStream,
      modelKey,
      promptKey,
      tools,
      supportsStreaming,
      tChat,
      tErrors,
      userId,
    ],
  );

  return {
    messages,
    isStreaming: isStreamingActive,
    isStreamingEnabled,
    isBusy,
    error,
    sendMessage,
    cancelStream,
    setIsStreamingEnabled,
  };
}
