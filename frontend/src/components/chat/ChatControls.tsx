"use client";

import { useTranslations } from "next-intl";
import { MCPToolSelector } from "@/components/ui/MCPToolSelector";
import type { McpServer, McpToolSelection } from "@/features/mcp";

interface ChatControlsProps {
  // Streaming control
  supportsStreaming: boolean;
  isStreamingEnabled: boolean;
  onStreamingToggle: (enabled: boolean) => void;

  // MCP tool selection
  mcpServers?: McpServer[];
  selectedTools: McpToolSelection[];
  onToolsChange: (tools: McpToolSelection[]) => void;
}

/**
 * Chat controls component
 * Contains streaming toggle and MCP tool selector
 */
export function ChatControls({
  supportsStreaming,
  isStreamingEnabled,
  onStreamingToggle,
  mcpServers,
  selectedTools,
  onToolsChange,
}: ChatControlsProps) {
  const t = useTranslations("common.chat");

  return (
    <div className="grid gap-3 md:grid-cols-2">
      {/* Streaming Toggle */}
      <div className="flex items-center justify-between rounded-2xl border border-white/10 bg-white/5 px-4 py-3 backdrop-blur-sm">
        <div className="flex items-center gap-2">
          <svg
            className="h-5 w-5 text-emerald-400"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M13 10V3L4 14h7v7l9-11h-7z"
            />
          </svg>
          <div>
            <p className="text-sm font-medium text-white">
              {t("streaming.label")}
            </p>
            <p className="text-xs text-white/60">
              {!supportsStreaming
                ? t("streaming.unsupported")
                : isStreamingEnabled
                  ? t("streaming.on")
                  : t("streaming.off")}
            </p>
          </div>
        </div>
        <button
          onClick={() => onStreamingToggle(!isStreamingEnabled)}
          disabled={!supportsStreaming}
          className={`relative h-6 w-11 rounded-full transition-colors ${
            isStreamingEnabled && supportsStreaming
              ? "bg-emerald-500"
              : "bg-white/20"
          } ${!supportsStreaming ? "cursor-not-allowed opacity-50" : "cursor-pointer"}`}
        >
          <span
            className={`absolute left-1 top-1 h-4 w-4 rounded-full bg-white transition-transform ${
              isStreamingEnabled && supportsStreaming ? "translate-x-5" : ""
            }`}
          />
        </button>
      </div>

      {/* MCP Tool Selector */}
      {mcpServers && mcpServers.length > 0 && (
        <MCPToolSelector
          servers={mcpServers}
          value={selectedTools}
          onChange={onToolsChange}
        />
      )}
    </div>
  );
}
