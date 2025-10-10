"use client";

import {
  FormEvent,
  useCallback,
  useEffect,
  useMemo,
  useRef,
  useState,
} from "react";
import { useTranslations } from "next-intl";
import { motion } from "framer-motion";

import { ApiError } from "@/lib/api/api-error";
import {
  ConversationMessage,
  ConversationReply,
  ConversationRequestInput,
  ConversationStreamChunk,
  streamConversationRequest,
  useConversationModels,
  useSetActiveModel,
} from "@/features/conversation";
import { useConversationMutation } from "@/features/conversation";
import { useFetchMcpServers } from "@/features/mcp";
import type { McpToolSelection } from "@/features/mcp";
import { ToolSelector } from "@/components/mcp/ToolSelector";
import { ChatMessage, ChatMessageLoading } from "./ChatMessage";
import { ModelSelector } from "@/components/ui/ModelSelector";
import { cn, staggerContainer } from "@/lib/utils";

type Translator = (
  key: string,
  values?: Record<string, string | number | Date>,
) => string;

type ChatMessage = ConversationMessage & {
  id: string;
};

type ChatShellProps = {
  title?: string;
  subtitle?: string;
  initialConversationId?: string;
  initialMessages?: ChatMessage[];
  defaultTools?: McpToolSelection[];
  userId?: string;
  modelKey?: string;
};

function toHistory(messages: ChatMessage[]): ConversationMessage[] {
  return messages
    .filter(({ content }) => content.trim().length > 0)
    .map(({ role, content }) => ({ role, content }));
}

function getErrorMessage(
  translateChat: Translator,
  translateErrors: Translator,
  error: unknown,
) {
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
      // ignore and fallback below
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

export function ChatShell({
  title,
  subtitle,
  initialConversationId,
  initialMessages = [],
  defaultTools,
  userId,
  modelKey,
}: ChatShellProps) {
  const tChat = useTranslations("common.chat");
  const tErrors = useTranslations("errors");

  const [conversationId] = useState(
    () => initialConversationId ?? crypto.randomUUID(),
  );
  const [messages, setMessages] = useState<ChatMessage[]>(initialMessages);
  const [inputValue, setInputValue] = useState("");
  const [formError, setFormError] = useState<string | null>(null);
  const [isStreamingEnabled, setIsStreamingEnabled] = useState(true);
  const [isStreamingActive, setIsStreamingActive] = useState(false);
  const [selectedModelKey, setSelectedModelKey] = useState<string | undefined>(
    modelKey,
  );
  const [selectedTools, setSelectedTools] = useState<McpToolSelection[]>(
    defaultTools ?? [],
  );
  const [historyIndex, setHistoryIndex] = useState(-1);

  const streamControllerRef = useRef<AbortController | null>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const mutation = useConversationMutation();
  const modelsQuery = useConversationModels();
  const mcpServersQuery = useFetchMcpServers();
  const setActiveModelMutation = useSetActiveModel();

  const models = modelsQuery.data.models;

  useEffect(() => {
    if (!models.length) {
      return;
    }

    const preferred =
      modelKey ?? modelsQuery.data.activeModelKey ?? models[0]?.key;

    setSelectedModelKey((current) => {
      if (current && models.some((item) => item.key === current)) {
        return current;
      }
      return preferred;
    });
  }, [modelKey, models, modelsQuery.data.activeModelKey]);

  const selectedModel = useMemo(
    () => models.find((item) => item.key === selectedModelKey),
    [models, selectedModelKey],
  );

  const supportsStreaming = Boolean(selectedModel?.supportsStreaming);

  useEffect(() => {
    if (!supportsStreaming && isStreamingEnabled) {
      setIsStreamingEnabled(false);
    }
  }, [supportsStreaming, isStreamingEnabled]);

  useEffect(
    () => () => {
      streamControllerRef.current?.abort();
    },
    [],
  );

  const hasMessages = messages.length > 0;

  const placeholder = useMemo(() => tChat("inputPlaceholder"), [tChat]);

  const isBusy = mutation.isPending || isStreamingActive;

  const resetStreamingController = useCallback(() => {
    if (streamControllerRef.current) {
      streamControllerRef.current.abort();
      streamControllerRef.current = null;
    }
    setIsStreamingActive(false);
  }, []);

  const handleSubmit = useCallback(
    async (event: FormEvent<HTMLFormElement>) => {
      event.preventDefault();
      if (isBusy) return;

      const trimmed = inputValue.trim();
      if (!trimmed) return;

      setFormError(null);
      setInputValue("");

      resetStreamingController();

      const userMessage: ChatMessage = {
        id: crypto.randomUUID(),
        role: "user",
        content: trimmed,
      };

      const nextMessages = [...messages, userMessage];
      const history = toHistory(nextMessages);

      const payload: ConversationRequestInput = {
        conversationId,
        history,
        userId,
        modelKey: selectedModelKey,
        tools: selectedTools.length > 0 ? selectedTools : undefined,
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

        const handleStreamError = (error: Error) => {
          streamControllerRef.current = null;
          setIsStreamingActive(false);
          setFormError(error.message || tChat("error.generic"));
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
        } catch (error) {
          setFormError(getErrorMessage(tChat, tErrors, error));
        }
      }
    },
    [
      conversationId,
      defaultTools,
      isBusy,
      isStreamingEnabled,
      inputValue,
      messages,
      mutation,
      resetStreamingController,
      selectedModelKey,
      supportsStreaming,
      tChat,
      tErrors,
      userId,
    ],
  );

  const handleToggleStreaming = useCallback(() => {
    if (!supportsStreaming) return;
    setIsStreamingEnabled((prev) => !prev);
  }, [supportsStreaming]);

  const handleModelChange = useCallback((value: string) => {
    setSelectedModelKey(value);
  }, []);

  const handleKeyDown = useCallback(
    (event: React.KeyboardEvent<HTMLTextAreaElement>) => {
      // Shift + Enter: 換行 (default behavior)
      if (event.shiftKey && event.key === "Enter") {
        return; // Let default behavior handle newline
      }

      // Enter without Shift: 提交
      if (event.key === "Enter" && !event.shiftKey) {
        event.preventDefault();
        if (!isBusy && inputValue.trim()) {
          const form = event.currentTarget.form;
          if (form) {
            form.requestSubmit();
          }
        }
        return;
      }

      // Arrow Up: 回到上一個用戶訊息
      if (event.key === "ArrowUp" && !inputValue && !isBusy) {
        event.preventDefault();
        const userMessages = messages.filter((m) => m.role === "user");
        if (userMessages.length === 0) return;

        const newIndex =
          historyIndex === -1
            ? userMessages.length - 1
            : Math.max(0, historyIndex - 1);

        setHistoryIndex(newIndex);
        setInputValue(userMessages[newIndex]?.content ?? "");
        return;
      }

      // Arrow Down: 前往下一個訊息或清空
      if (event.key === "ArrowDown" && historyIndex !== -1 && !isBusy) {
        event.preventDefault();
        const userMessages = messages.filter((m) => m.role === "user");

        const newIndex = historyIndex + 1;
        if (newIndex >= userMessages.length) {
          setHistoryIndex(-1);
          setInputValue("");
        } else {
          setHistoryIndex(newIndex);
          setInputValue(userMessages[newIndex]?.content ?? "");
        }
      }
    },
    [historyIndex, inputValue, isBusy, messages],
  );

  const handleInputChange = useCallback(
    (event: React.ChangeEvent<HTMLTextAreaElement>) => {
      setInputValue(event.target.value);
      // Reset history index when user types
      if (historyIndex !== -1) {
        setHistoryIndex(-1);
      }
    },
    [historyIndex],
  );

  const handleSetAsDefault = useCallback(() => {
    if (!selectedModelKey) return;

    setActiveModelMutation.mutate(selectedModelKey, {
      onSuccess: () => {
        // Success feedback handled by cache update
      },
      onError: (error) => {
        console.error("Failed to set active model:", error);
        setFormError(tChat("model.setAsDefaultError"));
      },
    });
  }, [selectedModelKey, setActiveModelMutation, tChat]);

  const isCurrentModelDefault =
    selectedModelKey === modelsQuery.data.activeModelKey;

  return (
    <motion.section
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.6, ease: "easeOut" }}
      className="flex flex-col gap-6"
    >
      {/* App Header */}
      {title && (
        <motion.header
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          className="space-y-2 text-center"
        >
          <h1 className="bg-gradient-to-b from-white via-white/90 to-white/60 bg-clip-text text-3xl font-bold text-transparent md:text-4xl">
            {title}
          </h1>
          {subtitle && (
            <p className="text-sm text-white/60 md:text-base">{subtitle}</p>
          )}
        </motion.header>
      )}

      {/* Chat Container */}
      <div className="rounded-3xl border border-white/10 bg-white/5 p-6 backdrop-blur-xl">
        {/* Status indicator */}
        {isBusy && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: "auto" }}
            className="mb-4 flex items-center gap-2 text-xs text-emerald-300"
          >
            <motion.span
              animate={{
                scale: [1, 1.2, 1],
                opacity: [0.5, 1, 0.5],
              }}
              transition={{
                duration: 1.5,
                repeat: Infinity,
                ease: "easeInOut",
              }}
              className="h-2 w-2 rounded-full bg-emerald-400"
            />
            <span>
              {isStreamingActive
                ? tChat("status.streaming")
                : tChat("status.generating")}
            </span>
          </motion.div>
        )}

        <motion.div
          variants={staggerContainer}
          initial="initial"
          animate="animate"
          className="flex max-h-[420px] flex-col gap-3 overflow-y-auto rounded-2xl border border-white/5 bg-neutral-950/60 p-4 backdrop-blur-sm scrollbar-thin scrollbar-track-white/5 scrollbar-thumb-white/20"
        >
          {hasMessages ? (
            messages.map((message, index) => (
              <ChatMessage
                key={message.id}
                message={message}
                userLabel={tChat("userLabel")}
                assistantLabel={tChat("assistantLabel")}
              />
            ))
          ) : (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="flex flex-1 items-center justify-center text-sm text-white/40"
            >
              {tChat("emptyState")}
            </motion.div>
          )}

          {isBusy ? (
            <ChatMessageLoading
              label={
                isStreamingActive
                  ? tChat("status.streaming")
                  : tChat("status.generating")
              }
              isStreaming={isStreamingActive}
            />
          ) : null}
        </motion.div>

        {/* Input Section with Model Selector */}
        <form className="flex flex-col gap-3" onSubmit={handleSubmit}>
          {/* Model Selector above input */}
          <div className="grid grid-cols-1 gap-3 md:grid-cols-2">
            <ModelSelector
              models={models}
              selectedModelKey={selectedModelKey}
              activeModelKey={modelsQuery.data.activeModelKey}
              onSelect={handleModelChange}
              onSetAsDefault={handleSetAsDefault}
              disabled={modelsQuery.isPending || !models.length}
              isPending={setActiveModelMutation.isPending}
              isCurrentModelDefault={isCurrentModelDefault}
            />

            {/* MCP Tool Selector */}
            {mcpServersQuery.data?.servers && (
              <ToolSelector
                servers={mcpServersQuery.data.servers}
                value={selectedTools}
                onChange={setSelectedTools}
              />
            )}
          </div>

          {/* Input Area */}
          <motion.div
            whileFocus={{ scale: 1.01 }}
            className="group flex items-start gap-3 rounded-2xl border border-white/10 bg-white/5 px-4 py-3 shadow-[0_12px_30px_-20px_rgba(59,130,246,0.5)] backdrop-blur-sm transition-all focus-within:border-emerald-500/30 focus-within:shadow-[0_12px_30px_-10px_rgba(16,185,129,0.3)]"
          >
            <textarea
              ref={textareaRef}
              className="flex-1 resize-none bg-transparent text-sm text-white/90 placeholder:text-white/40 focus:outline-none"
              placeholder={placeholder}
              value={inputValue}
              onChange={handleInputChange}
              onKeyDown={handleKeyDown}
              disabled={isBusy}
              rows={1}
              style={{
                minHeight: "1.5rem",
                maxHeight: "10rem",
                height: "auto",
              }}
              onInput={(e) => {
                const target = e.target as HTMLTextAreaElement;
                target.style.height = "auto";
                target.style.height = `${target.scrollHeight}px`;
              }}
            />
            <motion.button
              type="submit"
              disabled={isBusy || !inputValue.trim()}
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              className={cn(
                "inline-flex items-center gap-2 rounded-full bg-gradient-to-r from-emerald-400 to-emerald-500 px-5 py-2 text-sm font-semibold text-white shadow-lg transition-all",
                !isBusy && inputValue.trim()
                  ? "shadow-emerald-500/25 hover:shadow-xl hover:shadow-emerald-500/40"
                  : "pointer-events-none opacity-50",
              )}
            >
              <span>{tChat("send")}</span>
              <motion.svg
                className="h-4 w-4"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
                animate={
                  !isBusy && inputValue.trim() ? { x: [0, 2, 0] } : { x: 0 }
                }
                transition={{
                  duration: 1,
                  repeat: Infinity,
                  ease: "easeInOut",
                }}
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M13 7l5 5m0 0l-5 5m5-5H6"
                />
              </motion.svg>
            </motion.button>
          </motion.div>
          {formError ? (
            <motion.p
              initial={{ opacity: 0, y: -10 }}
              animate={{ opacity: 1, y: 0 }}
              className="text-xs text-red-300"
            >
              {formError}
            </motion.p>
          ) : null}
        </form>
      </div>
    </motion.section>
  );
}
