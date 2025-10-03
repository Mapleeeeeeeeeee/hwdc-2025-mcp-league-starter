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

import { ApiError } from "@/lib/api/api-error";
import {
  ConversationMessage,
  ConversationReply,
  ConversationRequestInput,
  ConversationStreamChunk,
  streamConversationRequest,
  useConversationModels,
} from "@/features/conversation";
import { useConversationMutation } from "@/features/conversation";

import type { McpToolSelection } from "@/features/mcp";

type Translator = (
  key: string,
  values?: Record<string, string | number | Date>,
) => string;

type ChatMessage = ConversationMessage & {
  id: string;
};

type ChatShellProps = {
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

  const streamControllerRef = useRef<AbortController | null>(null);

  const mutation = useConversationMutation();
  const modelsQuery = useConversationModels();

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
        tools: defaultTools,
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

  return (
    <section className="flex flex-col gap-4 rounded-3xl border border-white/10 bg-white/5 p-6">
      <header className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
        <div className="flex flex-col gap-2">
          <h2 className="text-lg font-semibold text-white/90">
            {tChat("title")}
          </h2>
          {isBusy ? (
            <span className="text-xs font-medium uppercase tracking-[0.3em] text-emerald-300">
              {isStreamingActive
                ? tChat("status.streaming")
                : tChat("status.pending")}
            </span>
          ) : null}
        </div>

        <div className="flex flex-wrap items-center gap-3 text-xs">
          <label className="flex items-center gap-2 rounded-full border border-white/10 bg-white/10/20 px-3 py-1 text-white/70">
            <span className="font-semibold uppercase tracking-[0.3em] text-white/50">
              {tChat("model.label")}
            </span>
            <select
              className="min-w-[9rem] bg-transparent text-white focus:outline-none"
              value={selectedModelKey ?? ""}
              onChange={(event) => handleModelChange(event.target.value)}
              disabled={modelsQuery.isPending || !models.length}
            >
              {modelsQuery.isPending ? (
                <option value="" disabled>
                  {tChat("model.loading")}
                </option>
              ) : null}
              {!models.length ? (
                <option value="" disabled>
                  {tChat("model.empty")}
                </option>
              ) : null}
              {models.map((model) => (
                <option
                  key={model.key}
                  value={model.key}
                  className="text-black"
                >
                  {`${model.key} · ${model.modelId}`}
                </option>
              ))}
            </select>
          </label>

          <button
            type="button"
            role="switch"
            aria-checked={isStreamingEnabled && supportsStreaming}
            aria-disabled={!supportsStreaming}
            onClick={handleToggleStreaming}
            className={`flex items-center gap-2 rounded-full border border-white/10 px-3 py-1 transition ${supportsStreaming ? "bg-emerald-400/20 text-emerald-100 hover:bg-emerald-300/30" : "cursor-not-allowed bg-white/10 text-white/40"}`}
          >
            <span className="font-semibold uppercase tracking-[0.3em]">
              {tChat("streaming.label")}
            </span>
            <span className="text-sm font-medium">
              {supportsStreaming
                ? tChat(isStreamingEnabled ? "streaming.on" : "streaming.off")
                : tChat("streaming.unsupported")}
            </span>
          </button>
        </div>
      </header>

      <div className="flex max-h-[420px] flex-col gap-3 overflow-y-auto rounded-2xl border border-white/5 bg-neutral-950/60 p-4">
        {hasMessages ? (
          messages.map((message) => (
            <article
              key={message.id}
              className={`flex flex-col gap-1 rounded-2xl border border-white/5 px-4 py-3 text-sm leading-relaxed shadow-[0_8px_20px_-12px_rgba(0,0,0,0.45)] ${message.role === "user" ? "self-end bg-emerald-500/10 text-emerald-100" : "self-start bg-white/10 text-white"}`}
            >
              <span className="text-xs font-semibold uppercase tracking-[0.3em] text-white/40">
                {message.role === "user"
                  ? tChat("userLabel")
                  : tChat("assistantLabel")}
              </span>
              <p>{message.content}</p>
            </article>
          ))
        ) : (
          <div className="flex flex-1 items-center justify-center text-sm text-white/40">
            {tChat("emptyState")}
          </div>
        )}

        {isBusy ? (
          <article className="w-fit rounded-2xl border border-white/10 bg-white/10 px-4 py-3 text-sm text-white/90">
            <span className="inline-flex items-center gap-2">
              <span className="size-2 animate-pulse rounded-full bg-white/70" />
              {isStreamingActive
                ? tChat("status.streaming")
                : tChat("status.generating")}
            </span>
          </article>
        ) : null}
      </div>

      <form className="flex flex-col gap-3" onSubmit={handleSubmit}>
        <div className="flex items-center gap-3 rounded-full border border-white/10 bg-white/5 px-4 py-2 shadow-[0_12px_30px_-20px_rgba(59,130,246,0.5)]">
          <input
            className="flex-1 bg-transparent text-sm text-white/90 placeholder:text-white/40 focus:outline-none"
            placeholder={placeholder}
            value={inputValue}
            onChange={(event) => setInputValue(event.target.value)}
            disabled={isBusy}
          />
          <button
            type="submit"
            disabled={isBusy || !inputValue.trim()}
            className="inline-flex items-center rounded-full bg-emerald-400 px-4 py-1.5 text-sm font-semibold text-emerald-950 transition hover:bg-emerald-300 disabled:pointer-events-none disabled:opacity-50"
          >
            {tChat("send")}
          </button>
        </div>
        {formError ? <p className="text-xs text-red-300">{formError}</p> : null}
      </form>
    </section>
  );
}
