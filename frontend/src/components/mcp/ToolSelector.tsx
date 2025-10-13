"use client";

import { useTranslations } from "next-intl";
import { useCallback, useState, useMemo } from "react";

import type { McpServer, McpToolSelection } from "@/features/mcp";

type ToolSelectorProps = {
  servers: McpServer[];
  value: McpToolSelection[];
  onChange: (tools: McpToolSelection[]) => void;
};

export function ToolSelector({ servers, value, onChange }: ToolSelectorProps) {
  const t = useTranslations("mcp.tools");
  const [isExpanded, setIsExpanded] = useState(false);

  // Get enabled and connected servers
  const availableServers = servers.filter(
    (server) => server.enabled && server.connected,
  );

  // Create a map of selected servers for quick lookup
  const selectedMap = useMemo(
    () => new Map(value.map((tool) => [tool.server, tool])),
    [value],
  );

  const toggleServer = useCallback(
    (serverName: string) => {
      const existing = selectedMap.get(serverName);

      if (existing) {
        // Remove server
        onChange(value.filter((tool) => tool.server !== serverName));
      } else {
        // Add server with all functions
        onChange([...value, { server: serverName }]);
      }
    },
    [value, selectedMap, onChange],
  );

  const toggleFunction = useCallback(
    (serverName: string, functionName: string) => {
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
        const newFunctions = currentFunctions.filter(
          (fn) => fn !== functionName,
        );
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
    },
    [value, selectedMap, onChange],
  );

  const selectAllServers = useCallback(() => {
    onChange(availableServers.map((server) => ({ server: server.name })));
  }, [availableServers, onChange]);

  const clearAll = useCallback(() => {
    onChange([]);
  }, [onChange]);

  const isServerSelected = (serverName: string) => selectedMap.has(serverName);

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

  if (availableServers.length === 0) {
    return null;
  }

  return (
    <div className="rounded-lg border border-white/10 bg-white/5 p-3">
      <button
        type="button"
        onClick={() => setIsExpanded(!isExpanded)}
        className="flex w-full items-center justify-between text-sm font-medium text-white/90"
      >
        <div className="flex items-center gap-2">
          <svg
            className="size-4"
            xmlns="http://www.w3.org/2000/svg"
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
          <span>{t("sectionTitle")}</span>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-xs text-white/50">
            {value.length === 0
              ? t("noServersSelected")
              : t("selectedCount", { count: value.length })}
          </span>
          <svg
            className={`size-4 transition-transform ${isExpanded ? "rotate-180" : ""}`}
            xmlns="http://www.w3.org/2000/svg"
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
          </svg>
        </div>
      </button>

      {isExpanded ? (
        <div className="mt-3 space-y-2">
          <div className="flex gap-2">
            <button
              type="button"
              onClick={selectAllServers}
              className="flex-1 rounded-md border border-white/10 bg-white/5 px-2 py-1 text-xs font-medium text-white/70 transition hover:bg-white/10"
            >
              {t("enableAll")}
            </button>
            <button
              type="button"
              onClick={clearAll}
              className="flex-1 rounded-md border border-white/10 bg-white/5 px-2 py-1 text-xs font-medium text-white/70 transition hover:bg-white/10"
            >
              {t("disableAll")}
            </button>
          </div>

          <div className="space-y-2">
            {availableServers.map((server) => {
              const selected = isServerSelected(server.name);
              const allFunctionsSelected = areAllFunctionsSelected(server.name);

              return (
                <div
                  key={server.name}
                  className="rounded-md border border-white/10 bg-white/5 p-2"
                >
                  <div className="flex items-center justify-between">
                    <button
                      type="button"
                      onClick={() => toggleServer(server.name)}
                      className="flex flex-1 items-center gap-2 text-left"
                    >
                      <div
                        className={`size-4 flex items-center justify-center rounded border ${
                          selected
                            ? "border-emerald-500/50 bg-emerald-500/20"
                            : "border-white/20 bg-white/5"
                        }`}
                      >
                        {selected ? (
                          <svg
                            className="size-3 text-emerald-400"
                            xmlns="http://www.w3.org/2000/svg"
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
                        ) : null}
                      </div>
                      <div className="flex-1">
                        <p className="text-sm font-medium text-white/90">
                          {server.name}
                        </p>
                        {server.description ? (
                          <p className="text-xs text-white/40">
                            {server.description}
                          </p>
                        ) : null}
                      </div>
                    </button>
                    <span className="text-xs text-white/40">
                      {server.functionCount} fn
                    </span>
                  </div>

                  {selected && server.functions.length > 0 ? (
                    <div className="mt-2 space-y-1 border-t border-white/10 pt-2">
                      <button
                        type="button"
                        onClick={() => {
                          if (allFunctionsSelected) {
                            // Deselect all by selecting none
                            onChange(
                              value.filter(
                                (tool) => tool.server !== server.name,
                              ),
                            );
                          } else {
                            // Select all functions
                            onChange(
                              value.map((tool) =>
                                tool.server === server.name
                                  ? { ...tool, functions: undefined }
                                  : tool,
                              ),
                            );
                          }
                        }}
                        className="w-full text-left text-xs font-medium text-white/60 hover:text-white/80"
                      >
                        {allFunctionsSelected
                          ? `✓ ${t("allFunctions")}`
                          : t("allFunctions")}
                      </button>
                      <div className="ml-3 space-y-1">
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
                              className="flex w-full items-center gap-2 rounded px-2 py-1 text-left text-xs text-white/60 transition hover:bg-white/5 hover:text-white/80"
                            >
                              <span
                                className={`size-1.5 rounded-full ${
                                  fnSelected ? "bg-emerald-400" : "bg-white/20"
                                }`}
                              />
                              {fn}
                            </button>
                          );
                        })}
                      </div>
                    </div>
                  ) : null}
                </div>
              );
            })}
          </div>
        </div>
      ) : null}
    </div>
  );
}
