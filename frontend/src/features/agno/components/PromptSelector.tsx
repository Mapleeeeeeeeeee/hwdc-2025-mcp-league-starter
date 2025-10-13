"use client";

import { useState, useRef, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { useTranslations } from "next-intl";
import { cn } from "@/lib/utils";

import { useAgnoConfig } from "../hooks";
import type { PromptConfig } from "../types";

type PromptSelectorProps = {
  value?: string;
  onChange: (promptKey: string | undefined) => void;
  className?: string;
};

/**
 * Dropdown selector for choosing a prompt preset
 * Styled to match the existing ModelSelector design
 */
export function PromptSelector({
  value,
  onChange,
  className = "",
}: PromptSelectorProps) {
  const { data: config, isLoading } = useAgnoConfig();
  const t = useTranslations("agno.prompts");
  const [isOpen, setIsOpen] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);

  const enabledPrompts = config?.prompts.filter((p) => p.enabled) ?? [];
  const selectedPrompt = enabledPrompts.find((p) => p.key === value);

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (
        containerRef.current &&
        !containerRef.current.contains(event.target as Node)
      ) {
        setIsOpen(false);
      }
    };

    if (isOpen) {
      document.addEventListener("mousedown", handleClickOutside);
    }

    return () => {
      document.removeEventListener("mousedown", handleClickOutside);
    };
  }, [isOpen]);

  if (isLoading) {
    return (
      <div
        className={cn(
          "flex items-center gap-2 rounded-xl border border-white/10 bg-white/5 px-4 py-2.5 backdrop-blur-sm",
          className,
        )}
      >
        <div className="h-4 w-4 animate-spin rounded-full border-2 border-white/20 border-t-white/60" />
        <span className="text-sm text-white/50">{t("loading")}</span>
      </div>
    );
  }

  if (enabledPrompts.length === 0) {
    return null;
  }

  return (
    <div ref={containerRef} className={cn("relative", className)}>
      {/* Trigger Button */}
      <button
        type="button"
        onClick={() => setIsOpen(!isOpen)}
        className={cn(
          "flex w-full items-center justify-between gap-3 rounded-xl border border-white/10 bg-white/5 px-4 py-2.5 text-left backdrop-blur-sm transition-all",
          isOpen && "border-purple-500/50 bg-white/10",
          "hover:border-white/20",
        )}
      >
        <div className="flex items-center gap-3">
          {/* Icon */}
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-gradient-to-br from-purple-500 to-pink-600 text-xs font-bold text-white">
            <svg
              className="h-5 w-5"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
              />
            </svg>
          </div>

          {/* Prompt Info */}
          <div className="flex flex-col">
            <span className="text-sm font-medium text-white">
              {selectedPrompt?.name || t("default")}
            </span>
            <span className="text-xs text-white/50">{t("sectionTitle")}</span>
          </div>
        </div>

        {/* Chevron Icon */}
        <motion.svg
          animate={{ rotate: isOpen ? 180 : 0 }}
          transition={{ duration: 0.2 }}
          className="h-5 w-5 text-white/50"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M19 9l-7 7-7-7"
          />
        </motion.svg>
      </button>

      {/* Dropdown Menu */}
      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ opacity: 0, y: -10, scale: 0.95 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: -10, scale: 0.95 }}
            transition={{ duration: 0.2 }}
            className="absolute left-0 right-0 top-full z-50 mt-2 max-h-[280px] overflow-y-auto rounded-xl border border-white/10 bg-neutral-900/95 p-2 shadow-2xl backdrop-blur-xl"
          >
            {/* Default Option */}
            <button
              type="button"
              onClick={() => {
                onChange(undefined);
                setIsOpen(false);
              }}
              className={cn(
                "flex w-full items-center gap-3 rounded-lg px-3 py-2.5 text-left transition-all",
                !value ? "bg-purple-500/10" : "hover:bg-white/5",
              )}
            >
              <div className="flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-lg bg-gradient-to-br from-gray-500 to-gray-600 text-xs font-bold text-white">
                D
              </div>
              <div className="flex flex-1 flex-col">
                <span
                  className={cn(
                    "text-sm font-medium",
                    !value ? "text-white" : "text-white/70",
                  )}
                >
                  {t("default")}
                </span>
                <span className="text-xs text-white/40">
                  {t("defaultDescription")}
                </span>
              </div>
              {!value && (
                <motion.svg
                  initial={{ scale: 0 }}
                  animate={{ scale: 1 }}
                  className="h-5 w-5 text-purple-400"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M5 13l4 4L19 7"
                  />
                </motion.svg>
              )}
            </button>

            {/* Prompt Options */}
            {enabledPrompts.map((prompt: PromptConfig) => {
              const isSelected = prompt.key === value;

              return (
                <button
                  key={prompt.key}
                  type="button"
                  onClick={() => {
                    onChange(prompt.key);
                    setIsOpen(false);
                  }}
                  className={cn(
                    "flex w-full items-center gap-3 rounded-lg px-3 py-2.5 text-left transition-all",
                    isSelected ? "bg-purple-500/10" : "hover:bg-white/5",
                  )}
                >
                  <div className="flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-lg bg-gradient-to-br from-purple-500 to-pink-600 text-xs font-bold text-white">
                    {prompt.name.charAt(0).toUpperCase()}
                  </div>
                  <div className="flex flex-1 flex-col">
                    <span
                      className={cn(
                        "text-sm font-medium",
                        isSelected ? "text-white" : "text-white/70",
                      )}
                    >
                      {prompt.name}
                    </span>
                    <span className="text-xs text-white/40">
                      {t("instructions", { count: prompt.instructionCount })}
                    </span>
                  </div>
                  {isSelected && (
                    <motion.svg
                      initial={{ scale: 0 }}
                      animate={{ scale: 1 }}
                      className="h-5 w-5 text-purple-400"
                      fill="none"
                      viewBox="0 0 24 24"
                      stroke="currentColor"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M5 13l4 4L19 7"
                      />
                    </motion.svg>
                  )}
                </button>
              );
            })}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
