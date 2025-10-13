"use client";

import { useState, useRef, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { useTranslations } from "next-intl";
import { cn } from "@/lib/utils";

import { useAgnoConfig } from "../hooks";
import type { ToolkitConfig } from "../types";

type ToolsSelectorProps = {
  value: string[];
  onChange: (selectedTools: string[]) => void;
  className?: string;
};

/**
 * Checkbox list for selecting which Agno tools to use
 * Styled to match the existing MCP tool selector design
 */
export function ToolsSelector({
  value,
  onChange,
  className = "",
}: ToolsSelectorProps) {
  const { data: config, isLoading } = useAgnoConfig();
  const t = useTranslations("agno.tools");
  const [isOpen, setIsOpen] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);

  const enabledToolkits = config?.toolkits.filter((t) => t.enabled) ?? [];
  const selectedCount = value.length;

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

  const handleToggle = (toolKey: string) => {
    if (value.includes(toolKey)) {
      onChange(value.filter((k) => k !== toolKey));
    } else {
      onChange([...value, toolKey]);
    }
  };

  const clearAll = () => {
    onChange([]);
  };

  const selectAll = () => {
    onChange(enabledToolkits.map((t) => t.key));
  };

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

  if (enabledToolkits.length === 0) {
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
          isOpen && "border-emerald-500/50 bg-white/10",
          "hover:border-white/20",
        )}
      >
        <div className="flex items-center gap-3">
          {/* Icon */}
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-gradient-to-br from-emerald-500 to-teal-600 text-white">
            <svg
              className="h-4 w-4"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M9 3v2m6-2v2M9 19v2m6-2v2M5 9H3m2 6H3m18-6h-2m2 6h-2M7 19h10a2 2 0 002-2V7a2 2 0 00-2-2H7a2 2 0 00-2 2v10a2 2 0 002 2zM9 9h6v6H9V9z"
              />
            </svg>
          </div>

          {/* Info */}
          <div className="flex flex-col">
            <span className="text-sm font-medium text-white">
              {t("sectionTitle")}
            </span>
            <span className="text-xs text-white/50">
              {selectedCount === 0
                ? t("noToolsSelected")
                : t("selectedCount", { count: selectedCount })}
            </span>
          </div>
        </div>

        {/* Chevron */}
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
            {/* Header with select/clear all */}
            <div className="mb-2 flex items-center justify-between border-b border-white/10 px-3 pb-2">
              <span className="text-xs font-medium text-white/60">
                {t("selectTools")}
              </span>
              <div className="flex gap-1">
                <button
                  type="button"
                  onClick={selectAll}
                  className="rounded px-2 py-0.5 text-xs text-emerald-400 hover:bg-emerald-400/10"
                >
                  {t("selectAll")}
                </button>
                <button
                  type="button"
                  onClick={clearAll}
                  className="rounded px-2 py-0.5 text-xs text-white/40 hover:bg-white/5"
                >
                  {t("clearAll")}
                </button>
              </div>
            </div>

            {/* Tool List */}
            <div className="space-y-1">
              {enabledToolkits.map((toolkit: ToolkitConfig) => {
                const isSelected = value.includes(toolkit.key);
                const displayName = toolkit.key
                  .replace(/_/g, " ")
                  .split(" ")
                  .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
                  .join(" ");

                return (
                  <button
                    key={toolkit.key}
                    type="button"
                    onClick={() => handleToggle(toolkit.key)}
                    className={cn(
                      "group flex w-full items-center gap-3 rounded-lg px-3 py-2.5 text-left transition-all",
                      isSelected ? "bg-emerald-500/10" : "hover:bg-white/5",
                    )}
                  >
                    {/* Checkbox */}
                    <div
                      className={cn(
                        "flex h-5 w-5 flex-shrink-0 items-center justify-center rounded border-2 transition-all",
                        isSelected
                          ? "border-emerald-400 bg-emerald-400"
                          : "border-white/30 bg-transparent group-hover:border-white/50",
                      )}
                    >
                      {isSelected && (
                        <motion.svg
                          initial={{ scale: 0 }}
                          animate={{ scale: 1 }}
                          className="h-3 w-3 text-white"
                          fill="none"
                          viewBox="0 0 24 24"
                          stroke="currentColor"
                        >
                          <path
                            strokeLinecap="round"
                            strokeLinejoin="round"
                            strokeWidth={3}
                            d="M5 13l4 4L19 7"
                          />
                        </motion.svg>
                      )}
                    </div>

                    {/* Tool Info */}
                    <div className="flex flex-1 flex-col">
                      <span
                        className={cn(
                          "text-sm font-medium",
                          isSelected ? "text-white" : "text-white/70",
                        )}
                      >
                        {displayName}
                      </span>
                      <span className="text-xs text-white/40">
                        {toolkit.toolkitClass?.split(".").pop() || "Agno Tool"}
                      </span>
                    </div>
                  </button>
                );
              })}
            </div>

            {/* Info Footer */}
            {value.length > 0 && (
              <div className="mt-2 border-t border-white/10 px-3 pt-2">
                <p className="text-xs text-white/40">{t("footer")}</p>
              </div>
            )}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
