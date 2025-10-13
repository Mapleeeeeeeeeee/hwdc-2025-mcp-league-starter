"use client";

import { FormEvent, useCallback, useMemo, useRef, useState } from "react";
import { useTranslations } from "next-intl";
import { motion } from "framer-motion";
import { cn } from "@/lib/utils";
import type { ConversationMessage } from "@/features/conversation";

interface ChatInputProps {
  onSubmit: (content: string) => void;
  disabled?: boolean;
  messages?: ConversationMessage[];
  error?: string | null;
}

/**
 * Chat input component with history navigation
 * Handles user input, keyboard shortcuts, and history browsing
 */
export function ChatInput({
  onSubmit,
  disabled = false,
  messages = [],
  error,
}: ChatInputProps) {
  const tChat = useTranslations("common.chat");
  const [inputValue, setInputValue] = useState("");
  const [historyIndex, setHistoryIndex] = useState(-1);
  const [isComposing, setIsComposing] = useState(false);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const placeholder = useMemo(() => tChat("inputPlaceholder"), [tChat]);

  const handleSubmit = useCallback(
    (event: FormEvent<HTMLFormElement>) => {
      event.preventDefault();
      if (disabled) return;

      const trimmed = inputValue.trim();
      if (!trimmed) return;

      onSubmit(trimmed);
      setInputValue("");
      setHistoryIndex(-1);
    },
    [disabled, inputValue, onSubmit],
  );

  const handleKeyDown = useCallback(
    (event: React.KeyboardEvent<HTMLTextAreaElement>) => {
      // Shift + Enter: newline (default behavior)
      if (event.shiftKey && event.key === "Enter") {
        return;
      }

      // Enter without Shift: submit (but not during IME composition)
      if (event.key === "Enter" && !event.shiftKey && !isComposing) {
        event.preventDefault();
        if (!disabled && inputValue.trim()) {
          const form = event.currentTarget.form;
          if (form) {
            form.requestSubmit();
          }
        }
        return;
      }

      // Arrow Up: previous user message
      if (event.key === "ArrowUp" && !inputValue && !disabled) {
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

      // Arrow Down: next message or clear
      if (event.key === "ArrowDown" && historyIndex !== -1 && !disabled) {
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
    [historyIndex, inputValue, disabled, messages, isComposing],
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

  // Handle composition events for IME (Chinese, Japanese, etc.)
  const handleCompositionStart = useCallback(() => {
    setIsComposing(true);
  }, []);

  const handleCompositionEnd = useCallback(() => {
    setIsComposing(false);
  }, []);

  return (
    <motion.div
      whileFocus={{ scale: 1.01 }}
      className="flex flex-col gap-3 rounded-2xl border border-white/10 bg-white/5 p-4 backdrop-blur-sm transition-all focus-within:border-emerald-500/50"
    >
      <form onSubmit={handleSubmit}>
        <textarea
          ref={textareaRef}
          value={inputValue}
          onChange={handleInputChange}
          onKeyDown={handleKeyDown}
          onCompositionStart={handleCompositionStart}
          onCompositionEnd={handleCompositionEnd}
          disabled={disabled}
          placeholder={placeholder}
          rows={3}
          className="w-full resize-none bg-transparent text-sm text-white placeholder-white/40 outline-none disabled:cursor-not-allowed disabled:opacity-50"
        />

        <div className="mt-3 flex items-center justify-between gap-3 border-t border-white/10 pt-3">
          <span className="text-xs text-white/40">{tChat("inputHint")}</span>
          <button
            type="submit"
            disabled={disabled || !inputValue.trim()}
            className={cn(
              "rounded-lg px-4 py-2 text-sm font-medium transition-all",
              disabled || !inputValue.trim()
                ? "cursor-not-allowed bg-white/10 text-white/40"
                : "bg-gradient-to-r from-emerald-500 to-teal-600 text-white hover:from-emerald-600 hover:to-teal-700 active:scale-95",
            )}
          >
            {tChat("send")}
          </button>
        </div>
      </form>

      {/* Error Message */}
      {error && (
        <motion.p
          initial={{ opacity: 0, y: -5 }}
          animate={{ opacity: 1, y: 0 }}
          className="text-xs text-red-300"
        >
          {error}
        </motion.p>
      )}
    </motion.div>
  );
}
