"use client";

import { useState, useRef, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { cn } from "@/lib/utils";
import type { LLMModelDescriptor } from "@/features/conversation";

interface ModelSelectorProps {
  models: LLMModelDescriptor[];
  selectedModelKey?: string;
  activeModelKey?: string;
  onSelect: (modelKey: string) => void;
  onSetAsDefault?: () => void;
  disabled?: boolean;
  isPending?: boolean;
}

/**
 * Modern model selector inspired by Perplexity AI
 * Clean, accessible, and intuitive design
 */
export function ModelSelector({
  models,
  selectedModelKey,
  activeModelKey,
  onSelect,
  onSetAsDefault,
  disabled = false,
  isPending = false,
}: ModelSelectorProps) {
  const [isOpen, setIsOpen] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);

  const selectedModel = models.find((m) => m.key === selectedModelKey);

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

  return (
    <div ref={containerRef} className="relative">
      {/* Trigger Button */}
      <button
        type="button"
        onClick={() => !disabled && setIsOpen(!isOpen)}
        disabled={disabled}
        className={cn(
          "flex w-full items-center justify-between gap-3 rounded-xl border border-white/10 bg-white/5 px-4 py-2.5 text-left backdrop-blur-sm transition-all",
          isOpen && "border-emerald-500/50 bg-white/10",
          !disabled && "hover:border-white/20",
          disabled && "cursor-not-allowed opacity-50",
        )}
      >
        <div className="flex items-center gap-3">
          {/* Model Icon */}
          <div
            className={cn(
              "flex h-8 w-8 items-center justify-center rounded-lg bg-gradient-to-br text-xs font-bold text-white",
              selectedModel?.key.includes("gpt")
                ? "from-emerald-500 to-teal-600"
                : selectedModel?.key.includes("claude")
                  ? "from-purple-500 to-blue-600"
                  : "from-orange-500 to-red-600",
            )}
          >
            {selectedModel?.key.charAt(0).toUpperCase() || "?"}
          </div>

          {/* Model Info */}
          <div className="flex flex-col">
            <span className="text-sm font-medium text-white">
              {selectedModel?.key || "Select Model"}
            </span>
            {selectedModel && (
              <span className="text-xs text-white/50">
                {selectedModel.modelId}
                {selectedModel.key === activeModelKey && " · 預設"}
              </span>
            )}
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
            className="absolute left-0 right-0 top-full z-50 mt-2 max-h-[320px] overflow-y-auto rounded-xl border border-white/10 bg-neutral-900/95 p-2 shadow-2xl backdrop-blur-xl"
          >
            {models.map((model) => {
              const isSelected = model.key === selectedModelKey;
              const isDefault = model.key === activeModelKey;

              return (
                <div
                  key={model.key}
                  className={cn(
                    "group relative flex w-full items-center gap-3 rounded-lg px-3 py-2.5 transition-all",
                    isSelected ? "bg-emerald-500/10" : "hover:bg-white/5",
                  )}
                >
                  {/* Model Selection Button */}
                  <button
                    type="button"
                    onClick={() => {
                      onSelect(model.key);
                      setIsOpen(false);
                    }}
                    className="flex flex-1 items-center gap-3 text-left"
                  >
                    {/* Model Icon */}
                    <div
                      className={cn(
                        "flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-lg bg-gradient-to-br text-xs font-bold text-white",
                        model.key.includes("gpt")
                          ? "from-emerald-500 to-teal-600"
                          : model.key.includes("claude")
                            ? "from-purple-500 to-blue-600"
                            : "from-orange-500 to-red-600",
                      )}
                    >
                      {model.key.charAt(0).toUpperCase()}
                    </div>

                    {/* Model Info */}
                    <div className="flex flex-1 flex-col">
                      <div className="flex items-center gap-2">
                        <span
                          className={cn(
                            "text-sm font-medium",
                            isSelected ? "text-white" : "text-white/70",
                          )}
                        >
                          {model.key}
                        </span>
                        {isDefault && (
                          <span className="rounded-full bg-blue-500/20 px-2 py-0.5 text-[10px] font-semibold text-blue-300">
                            預設
                          </span>
                        )}
                      </div>
                      <span className="text-xs text-white/40">
                        {model.modelId}
                      </span>
                    </div>

                    {/* Selected Indicator */}
                    {isSelected && (
                      <motion.svg
                        initial={{ scale: 0 }}
                        animate={{ scale: 1 }}
                        className="h-5 w-5 text-emerald-400"
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

                  {/* Set as Default Star Button - Now beside each model */}
                  {isSelected && !isDefault && onSetAsDefault && (
                    <motion.button
                      initial={{ opacity: 0, scale: 0.8 }}
                      animate={{ opacity: 1, scale: 1 }}
                      type="button"
                      onClick={(e) => {
                        e.stopPropagation();
                        onSetAsDefault();
                      }}
                      disabled={isPending}
                      className="flex items-center justify-center rounded-lg p-1.5 text-yellow-400 transition-all hover:bg-yellow-400/10 disabled:cursor-not-allowed disabled:opacity-50"
                      title="設為預設模型"
                    >
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
                          d="M11.049 2.927c.3-.921 1.603-.921 1.902 0l1.519 4.674a1 1 0 00.95.69h4.915c.969 0 1.371 1.24.588 1.81l-3.976 2.888a1 1 0 00-.363 1.118l1.518 4.674c.3.922-.755 1.688-1.538 1.118l-3.976-2.888a1 1 0 00-1.176 0l-3.976 2.888c-.783.57-1.838-.197-1.538-1.118l1.518-4.674a1 1 0 00-.363-1.118l-3.976-2.888c-.784-.57-.38-1.81.588-1.81h4.914a1 1 0 00.951-.69l1.519-4.674z"
                        />
                      </svg>
                    </motion.button>
                  )}
                </div>
              );
            })}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
