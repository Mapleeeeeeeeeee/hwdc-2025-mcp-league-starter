"use client";

import { FormEvent, useCallback, useMemo, useState } from "react";
import { useTranslations } from "next-intl";

import { ApiError } from "@/lib/api/api-error";
import {
  ConversationMessage,
  ConversationReply,
  ConversationRequestInput,
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
  return messages.map(({ role, content }) => ({ role, content }));
}

function getErrorMessage(
  translateChat: Translator,
  translateErrors: Translator,
  error: unknown,
) {
  if (!(error instanceof ApiError)) {
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

  const mutation = useConversationMutation();

  const hasMessages = messages.length > 0;

  const placeholder = useMemo(() => tChat("inputPlaceholder"), [tChat]);

  const handleSubmit = useCallback(
    async (event: FormEvent<HTMLFormElement>) => {
      event.preventDefault();
      if (mutation.isPending) return;

      const trimmed = inputValue.trim();
      if (!trimmed) return;

      setFormError(null);
      setInputValue("");

      const userMessage: ChatMessage = {
        id: crypto.randomUUID(),
        role: "user",
        content: trimmed,
      };

      setMessages((prev) => [...prev, userMessage]);

      const history = toHistory([...messages, userMessage]);

      const payload: ConversationRequestInput = {
        conversationId,
        history,
        userId,
        modelKey,
        tools: defaultTools,
      };

      try {
        const reply = await mutation.mutateAsync(payload);
        setMessages((prev) => appendAssistantMessage(prev, reply));
      } catch (error) {
        setFormError(getErrorMessage(tChat, tErrors, error));
      }
    },
    [
      conversationId,
      defaultTools,
      inputValue,
      messages,
      modelKey,
      mutation,
      tChat,
      tErrors,
      userId,
    ],
  );

  return (
    <section className="flex flex-col gap-4 rounded-3xl border border-white/10 bg-white/5 p-6">
      <header className="flex items-center justify-between">
        <h2 className="text-lg font-semibold text-white/90">
          {tChat("title")}
        </h2>
        {mutation.isPending ? (
          <span className="text-xs font-medium uppercase tracking-[0.3em] text-emerald-300">
            {tChat("status.pending")}
          </span>
        ) : null}
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

        {mutation.isPending ? (
          <article className="w-fit rounded-2xl border border-white/10 bg-white/10 px-4 py-3 text-sm text-white/90">
            <span className="inline-flex items-center gap-2">
              <span className="size-2 animate-pulse rounded-full bg-white/70" />
              {tChat("status.generating")}
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
            disabled={mutation.isPending}
          />
          <button
            type="submit"
            disabled={mutation.isPending || !inputValue.trim()}
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
