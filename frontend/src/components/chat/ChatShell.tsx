"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { useTranslations } from "next-intl";
import { motion } from "framer-motion";

import {
  useConversationModels,
  useSetActiveModel,
} from "@/features/conversation";
import { useFetchMcpServers } from "@/features/mcp";
import type { McpToolSelection } from "@/features/mcp";
import { useConversation } from "@/features/conversation/hooks/useConversation";
import { ChatMessage, ChatMessageLoading } from "./ChatMessage";
import { ChatInput } from "./ChatInput";
import { ChatControls } from "./ChatControls";
import { staggerContainer } from "@/lib/utils";

import type { ConversationMessage } from "@/features/conversation";

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

/**
 * Main chat interface component
 * Orchestrates conversation flow and UI components
 */
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

  const [conversationId] = useState(
    () => initialConversationId ?? crypto.randomUUID(),
  );
  const [selectedModelKey, setSelectedModelKey] = useState<string | undefined>(
    modelKey,
  );
  const [selectedTools, setSelectedTools] = useState<McpToolSelection[]>(
    defaultTools ?? [],
  );
  const [promptKey, setPromptKey] = useState<string | undefined>();
  const [selectedAgnoTools, setSelectedAgnoTools] = useState<string[]>([]);

  // Queries
  const modelsQuery = useConversationModels();
  const mcpServersQuery = useFetchMcpServers();
  const setActiveModelMutation = useSetActiveModel();

  const models = modelsQuery.data.models;
  const activeModelKey = modelsQuery.data.activeModelKey;

  // Initialize selected model
  useEffect(() => {
    if (!models.length) return;

    const preferred = modelKey ?? activeModelKey ?? models[0]?.key;

    setSelectedModelKey((current) => {
      if (current && models.some((item) => item.key === current)) {
        return current;
      }
      return preferred;
    });
  }, [modelKey, models, activeModelKey]);

  const selectedModel = useMemo(
    () => models.find((item) => item.key === selectedModelKey),
    [models, selectedModelKey],
  );

  const supportsStreaming = Boolean(selectedModel?.supportsStreaming);

  // Conversation hook
  const { messages, isStreaming, isBusy, error, sendMessage } = useConversation(
    {
      conversationId,
      initialMessages,
      userId,
      modelKey: selectedModelKey,
      promptKey,
      tools: selectedTools,
      supportsStreaming,
    },
  );

  // Send message directly without frontend enhancement
  const handleSendMessage = useCallback(
    (content: string) => {
      sendMessage(content);
    },
    [sendMessage],
  );

  const hasMessages = messages.length > 0;

  // Handlers
  const handleSetAsDefault = useCallback(() => {
    if (!selectedModelKey) return;

    setActiveModelMutation.mutate(selectedModelKey, {
      onError: (err) => {
        console.error("Failed to set active model:", err);
      },
    });
  }, [selectedModelKey, setActiveModelMutation]);

  const availableServers = useMemo(
    () =>
      mcpServersQuery.data?.servers.filter(
        (server) => server.enabled && server.connected,
      ) ?? [],
    [mcpServersQuery.data?.servers],
  );

  return (
    <motion.section
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.6, ease: "easeOut" }}
      className="flex flex-col gap-6"
    >
      {/* Header */}
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
              {isStreaming
                ? tChat("status.streaming")
                : tChat("status.generating")}
            </span>
          </motion.div>
        )}

        {/* Messages */}
        <motion.div
          variants={staggerContainer}
          initial="hidden"
          animate="visible"
          className="mb-6 min-h-[500px] max-h-[70vh] space-y-4 overflow-y-auto rounded-2xl border border-white/5 bg-neutral-950/50 p-6"
        >
          {!hasMessages && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="flex h-full items-center justify-center text-center text-white/40"
            >
              <div>
                <svg
                  className="mx-auto mb-4 h-16 w-16 opacity-50"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={1.5}
                    d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z"
                  />
                </svg>
                <p className="text-sm">{tChat("placeholder")}</p>
              </div>
            </motion.div>
          )}

          {messages.map((message) => (
            <ChatMessage
              key={message.id}
              message={message}
              userLabel={tChat("user")}
              assistantLabel={tChat("assistant")}
            />
          ))}

          {isBusy && !isStreaming && (
            <ChatMessageLoading label={tChat("assistant")} />
          )}
        </motion.div>

        {/* Controls */}
        <div className="space-y-4">
          <ChatControls
            models={models}
            selectedModelKey={selectedModelKey}
            activeModelKey={activeModelKey}
            onModelSelect={setSelectedModelKey}
            onSetAsDefault={handleSetAsDefault}
            isSettingDefault={setActiveModelMutation.isPending}
            mcpServers={availableServers}
            selectedTools={selectedTools}
            onToolsChange={setSelectedTools}
            promptKey={promptKey}
            onPromptKeyChange={setPromptKey}
            selectedAgnoTools={selectedAgnoTools}
            onAgnoToolsChange={setSelectedAgnoTools}
          />

          {/* Input */}
          <ChatInput
            onSubmit={handleSendMessage}
            disabled={isBusy}
            messages={messages}
            error={error}
          />
        </div>
      </div>
    </motion.section>
  );
}
