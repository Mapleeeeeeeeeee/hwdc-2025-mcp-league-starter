"use client";

import { motion, AnimatePresence } from "framer-motion";
import { useEffect } from "react";
import { ServerOverview } from "./ServerOverview";
import type { McpServersSnapshot } from "@/features/mcp";

interface MCPSettingsDrawerProps {
  isOpen: boolean;
  onClose: () => void;
  initialData?: McpServersSnapshot;
}

/**
 * MCP Settings Drawer Component
 * 從右側滑出的設定面板，用於顯示 MCP 伺服器狀態
 * 遵循 UI Guidelines 使用 Drawer/Sheet 結構
 */
export function MCPSettingsDrawer({
  isOpen,
  onClose,
  initialData,
}: MCPSettingsDrawerProps) {
  // Close on Escape key
  useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === "Escape" && isOpen) {
        onClose();
      }
    };

    document.addEventListener("keydown", handleEscape);
    return () => document.removeEventListener("keydown", handleEscape);
  }, [isOpen, onClose]);

  // Prevent body scroll when drawer is open
  useEffect(() => {
    if (isOpen) {
      document.body.style.overflow = "hidden";
    } else {
      document.body.style.overflow = "unset";
    }
    return () => {
      document.body.style.overflow = "unset";
    };
  }, [isOpen]);

  return (
    <AnimatePresence>
      {isOpen && (
        <>
          {/* Backdrop */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.2 }}
            onClick={onClose}
            className="fixed inset-0 z-40 bg-black/60 backdrop-blur-sm"
            aria-hidden="true"
          />

          {/* Drawer */}
          <motion.div
            initial={{ x: "100%" }}
            animate={{ x: 0 }}
            exit={{ x: "100%" }}
            transition={{
              duration: 0.3,
              ease: [0.4, 0, 0.2, 1],
            }}
            className="fixed right-0 top-0 z-50 h-full w-full max-w-md overflow-hidden bg-neutral-900 shadow-2xl sm:max-w-lg"
            role="dialog"
            aria-modal="true"
            aria-labelledby="drawer-title"
          >
            {/* Drawer Header */}
            <div className="flex items-center justify-between border-b border-white/10 bg-white/5 px-6 py-4">
              <h2
                id="drawer-title"
                className="text-lg font-semibold text-white"
              >
                MCP 設定
              </h2>
              <button
                type="button"
                onClick={onClose}
                className="rounded-lg p-2 text-white/60 transition hover:bg-white/10 hover:text-white"
                aria-label="關閉設定面板"
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
                    d="M6 18L18 6M6 6l12 12"
                  />
                </svg>
              </button>
            </div>

            {/* Drawer Content */}
            <div className="h-[calc(100%-73px)] overflow-y-auto p-6">
              <ServerOverview initialData={initialData} />
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
}
