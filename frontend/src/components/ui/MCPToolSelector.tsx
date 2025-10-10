"use client";

import { useState, useRef, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { useTranslations } from "next-intl";
import { cn } from "@/lib/utils";
import type { McpServer, McpToolSelection } from "@/features/mcp";

interface MCPToolSelectorProps {
  servers: McpServer[];
  value: McpToolSelection[];
  onChange: (tools: McpToolSelection[]) => void;
}

/**
 * Modern MCP tool selector with dropdown interface
 * Supports both server-level and individual function selection
 */
export function MCPToolSelector({
  servers,
  value,
  onChange,
}: MCPToolSelectorProps) {
  const t = useTranslations("mcp.tools");
  const [isOpen, setIsOpen] = useState(false);
  const [expandedServers, setExpandedServers] = useState<Set<string>>(
    new Set(),
  );
  const containerRef = useRef<HTMLDivElement>(null);

  // Get enabled and connected servers
  const availableServers = servers.filter(
    (server) => server.enabled && server.connected,
  );

  // Create a map of selected servers for quick lookup
  const selectedMap = new Map(value.map((tool) => [tool.server, tool]));

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

  const toggleServer = (serverName: string) => {
    const existing = selectedMap.get(serverName);

    if (existing) {
      onChange(value.filter((tool) => tool.server !== serverName));
    } else {
      onChange([...value, { server: serverName }]);
    }
  };

  const toggleFunction = (serverName: string, functionName: string) => {
    const existing = selectedMap.get(serverName);

    if (!existing) {
      // Server not selected, select it with this function
      onChange([...value, { server: serverName, functions: [functionName] }]);
      return;
    }

    const currentFunctions = existing.functions || [];

    if (currentFunctions.length === 0) {
      // All functions were selected, now select only this function
      onChange(
        value.map((tool) =>
          tool.server === serverName
            ? { ...tool, functions: [functionName] }
            : tool,
        ),
      );
    } else if (currentFunctions.includes(functionName)) {
      // Remove this function
      const newFunctions = currentFunctions.filter((fn) => fn !== functionName);
      if (newFunctions.length === 0) {
        // No functions left, remove the server
        onChange(value.filter((tool) => tool.server !== serverName));
      } else {
        onChange(
          value.map((tool) =>
            tool.server === serverName
              ? { ...tool, functions: newFunctions }
              : tool,
          ),
        );
      }
    } else {
      // Add this function
      onChange(
        value.map((tool) =>
          tool.server === serverName
            ? { ...tool, functions: [...currentFunctions, functionName] }
            : tool,
        ),
      );
    }
  };

  const isFunctionSelected = (serverName: string, functionName: string) => {
    const tool = selectedMap.get(serverName);
    if (!tool) return false;
    if (!tool.functions || tool.functions.length === 0) return true; // All functions
    return tool.functions.includes(functionName);
  };

  const areAllFunctionsSelected = (serverName: string) => {
    const tool = selectedMap.get(serverName);
    if (!tool) return false;
    return !tool.functions || tool.functions.length === 0;
  };

  const toggleServerExpanded = (serverName: string) => {
    const newExpanded = new Set(expandedServers);
    if (newExpanded.has(serverName)) {
      newExpanded.delete(serverName);
    } else {
      newExpanded.add(serverName);
    }
    setExpandedServers(newExpanded);
  };

  const clearAll = () => {
    onChange([]);
  };

  const selectAll = () => {
    onChange(availableServers.map((server) => ({ server: server.name })));
  };

  if (availableServers.length === 0) {
    return null;
  }

  return (
    <div ref={containerRef} className="relative">
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
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-gradient-to-br from-blue-500 to-purple-600 text-white">
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
                ? t("noServersSelected")
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
            className="absolute left-0 right-0 top-full z-50 mt-2 max-h-[400px] overflow-y-auto rounded-xl border border-white/10 bg-neutral-900/95 p-2 shadow-2xl backdrop-blur-xl"
          >
            {/* Quick Actions */}
            <div className="mb-2 flex gap-2 border-b border-white/10 pb-2">
              <button
                type="button"
                onClick={selectAll}
                className="flex-1 rounded-lg bg-emerald-500/10 px-3 py-1.5 text-xs font-medium text-emerald-300 transition-all hover:bg-emerald-500/20"
              >
                {t("enableAll")}
              </button>
              <button
                type="button"
                onClick={clearAll}
                className="flex-1 rounded-lg bg-red-500/10 px-3 py-1.5 text-xs font-medium text-red-300 transition-all hover:bg-red-500/20"
              >
                {t("disableAll")}
              </button>
            </div>

            {/* Server List */}
            <div className="space-y-1">
              {availableServers.map((server) => {
                const isSelected = selectedMap.has(server.name);
                const isExpanded = expandedServers.has(server.name);
                const allSelected = areAllFunctionsSelected(server.name);

                return (
                  <div key={server.name} className="rounded-lg">
                    {/* Server Row */}
                    <div
                      className={cn(
                        "group relative flex w-full items-center gap-3 rounded-lg px-3 py-2.5 transition-all",
                        isSelected ? "bg-emerald-500/10" : "hover:bg-white/5",
                      )}
                    >
                      {/* Server Checkbox */}
                      <button
                        type="button"
                        onClick={() => toggleServer(server.name)}
                        className="flex items-center gap-3"
                      >
                        <div
                          className={cn(
                            "flex h-5 w-5 flex-shrink-0 items-center justify-center rounded border-2 transition-all",
                            isSelected
                              ? "border-emerald-500 bg-emerald-500"
                              : "border-white/30 bg-transparent",
                          )}
                        >
                          {isSelected && (
                            <svg
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
                            </svg>
                          )}
                        </div>
                      </button>

                      {/* Server Info */}
                      <div className="flex flex-1 flex-col">
                        <span
                          className={cn(
                            "text-sm font-medium",
                            isSelected ? "text-white" : "text-white/70",
                          )}
                        >
                          {server.name}
                        </span>
                        {server.description && (
                          <span className="text-xs text-white/40">
                            {server.description}
                          </span>
                        )}
                      </div>

                      {/* Function Count Badge */}
                      <span className="rounded-full bg-white/10 px-2 py-0.5 text-xs text-white/60">
                        {server.functionCount} fn
                      </span>

                      {/* Expand Button */}
                      {server.functions.length > 0 && (
                        <button
                          type="button"
                          onClick={() => toggleServerExpanded(server.name)}
                          className="p-1 hover:bg-white/10 rounded"
                        >
                          <motion.svg
                            animate={{ rotate: isExpanded ? 180 : 0 }}
                            transition={{ duration: 0.2 }}
                            className="h-4 w-4 text-white/50"
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
                      )}
                    </div>

                    {/* Function List */}
                    {isExpanded && server.functions.length > 0 && (
                      <motion.div
                        initial={{ height: 0, opacity: 0 }}
                        animate={{ height: "auto", opacity: 1 }}
                        exit={{ height: 0, opacity: 0 }}
                        className="ml-8 mt-1 space-y-1 overflow-hidden border-l-2 border-white/10 pl-3"
                      >
                        {/* Select All Functions Button */}
                        <button
                          type="button"
                          onClick={() => {
                            if (!isSelected) {
                              // Server not selected, select it with all functions
                              onChange([...value, { server: server.name }]);
                            } else {
                              // Server selected, toggle all functions
                              onChange(
                                value.map((tool) =>
                                  tool.server === server.name
                                    ? { ...tool, functions: undefined }
                                    : tool,
                                ),
                              );
                            }
                          }}
                          className="flex w-full items-center gap-2 rounded px-2 py-1.5 text-left text-xs transition hover:bg-white/5"
                        >
                          <div
                            className={cn(
                              "flex h-3 w-3 items-center justify-center rounded-sm border",
                              allSelected
                                ? "border-blue-500 bg-blue-500"
                                : "border-white/30",
                            )}
                          >
                            {allSelected && (
                              <svg
                                className="h-2 w-2 text-white"
                                fill="none"
                                viewBox="0 0 24 24"
                                stroke="currentColor"
                              >
                                <path
                                  strokeLinecap="round"
                                  strokeLinejoin="round"
                                  strokeWidth={4}
                                  d="M5 13l4 4L19 7"
                                />
                              </svg>
                            )}
                          </div>
                          <span className="font-medium text-white/60">
                            {t("allFunctions")}
                          </span>
                        </button>

                        {/* Individual Functions */}
                        {server.functions.map((fn) => {
                          const fnSelected = isFunctionSelected(
                            server.name,
                            fn,
                          );
                          return (
                            <button
                              key={fn}
                              type="button"
                              onClick={() => toggleFunction(server.name, fn)}
                              className="flex w-full items-center gap-2 rounded px-2 py-1.5 text-left text-xs transition hover:bg-white/5"
                            >
                              <div
                                className={cn(
                                  "flex h-3 w-3 items-center justify-center rounded-sm border",
                                  fnSelected
                                    ? "border-emerald-500 bg-emerald-500"
                                    : "border-white/30",
                                )}
                              >
                                {fnSelected && (
                                  <svg
                                    className="h-2 w-2 text-white"
                                    fill="none"
                                    viewBox="0 0 24 24"
                                    stroke="currentColor"
                                  >
                                    <path
                                      strokeLinecap="round"
                                      strokeLinejoin="round"
                                      strokeWidth={4}
                                      d="M5 13l4 4L19 7"
                                    />
                                  </svg>
                                )}
                              </div>
                              <span className="text-white/60">{fn}</span>
                            </button>
                          );
                        })}
                      </motion.div>
                    )}
                  </div>
                );
              })}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
