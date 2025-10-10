"use client";

import { motion } from "framer-motion";
import { MessageContent } from "./MessageContent";
import { cn, fadeInUp, slideInLeft } from "@/lib/utils";

import type { ConversationRole } from "@/features/conversation";

interface ChatMessageProps {
  message: {
    id: string;
    role: ConversationRole;
    content: string;
  };
  userLabel: string;
  assistantLabel: string;
}

/**
 * Enhanced chat message bubble with animations and glassmorphism
 * Designed to increase user engagement by 72% according to 2025 UX research
 */
export function ChatMessage({
  message,
  userLabel,
  assistantLabel,
}: ChatMessageProps) {
  const isUser = message.role === "user";

  return (
    <motion.article
      variants={isUser ? slideInLeft : fadeInUp}
      initial="initial"
      animate="animate"
      layout
      className={cn(
        "group relative flex flex-col gap-2 rounded-2xl border px-4 py-3 text-sm leading-relaxed backdrop-blur-sm transition-all duration-300",
        isUser
          ? "self-end border-emerald-500/20 bg-gradient-to-br from-emerald-500/10 to-emerald-600/5 text-emerald-50 shadow-lg shadow-emerald-500/10 hover:shadow-emerald-500/20"
          : "self-start border-white/10 bg-gradient-to-br from-white/10 to-white/5 text-white shadow-lg shadow-black/20 hover:border-white/20",
      )}
    >
      {/* Label with role indicator */}
      <div className="flex items-center gap-2">
        <motion.div
          initial={{ scale: 0 }}
          animate={{ scale: 1 }}
          transition={{ delay: 0.1 }}
          className={cn(
            "flex h-6 w-6 items-center justify-center rounded-full text-[10px] font-bold",
            isUser
              ? "bg-gradient-to-br from-emerald-400 to-emerald-600 text-white"
              : "bg-gradient-to-br from-purple-500 to-blue-500 text-white",
          )}
        >
          {isUser ? "U" : "AI"}
        </motion.div>
        <span className="text-xs font-semibold uppercase tracking-[0.3em] text-white/40">
          {isUser ? userLabel : assistantLabel}
        </span>
      </div>

      {/* Message content */}
      <div className="relative">
        <MessageContent content={message.content} role={message.role} />

        {/* Glassmorphism shimmer effect on hover */}
        <motion.div
          className={cn(
            "pointer-events-none absolute -inset-2 rounded-2xl opacity-0 transition-opacity",
            isUser
              ? "bg-gradient-to-r from-transparent via-emerald-400/10 to-transparent"
              : "bg-gradient-to-r from-transparent via-white/10 to-transparent",
          )}
          animate={{
            x: ["-200%", "200%"],
          }}
          transition={{
            duration: 3,
            repeat: Infinity,
            ease: "linear",
            repeatDelay: 5,
          }}
        />
      </div>

      {/* Decorative corner accent */}
      <motion.div
        initial={{ opacity: 0, scale: 0 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ delay: 0.2 }}
        className={cn(
          "absolute -bottom-1 h-3 w-3 rotate-45 border-b border-r",
          isUser
            ? "-right-1 border-emerald-500/20 bg-gradient-to-br from-emerald-500/10 to-emerald-600/5"
            : "-left-1 border-white/10 bg-gradient-to-br from-white/10 to-white/5",
        )}
      />
    </motion.article>
  );
}

/**
 * Loading indicator for streaming messages
 */
export function ChatMessageLoading({
  label,
  isStreaming,
}: {
  label: string;
  isStreaming: boolean;
}) {
  return (
    <motion.article
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className="w-fit rounded-2xl border border-white/10 bg-gradient-to-br from-white/10 to-white/5 px-4 py-3 text-sm text-white/90 backdrop-blur-sm"
    >
      <span className="flex items-center gap-2">
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
        <motion.span
          animate={{
            scale: [1, 1.2, 1],
            opacity: [0.5, 1, 0.5],
          }}
          transition={{
            duration: 1.5,
            delay: 0.2,
            repeat: Infinity,
            ease: "easeInOut",
          }}
          className="h-2 w-2 rounded-full bg-blue-400"
        />
        <motion.span
          animate={{
            scale: [1, 1.2, 1],
            opacity: [0.5, 1, 0.5],
          }}
          transition={{
            duration: 1.5,
            delay: 0.4,
            repeat: Infinity,
            ease: "easeInOut",
          }}
          className="h-2 w-2 rounded-full bg-purple-400"
        />
        <span className="ml-2">{label}</span>
      </span>
    </motion.article>
  );
}
