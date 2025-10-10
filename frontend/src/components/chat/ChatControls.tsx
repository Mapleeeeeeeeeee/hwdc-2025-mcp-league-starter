"use client";

import { ModelSelector } from "@/components/ui/ModelSelector";
import { MCPToolSelector } from "@/components/ui/MCPToolSelector";
import type { LLMModelDescriptor } from "@/features/conversation";
import type { McpServer, McpToolSelection } from "@/features/mcp";

interface ChatControlsProps {
  // Model selection
  models: LLMModelDescriptor[];
  selectedModelKey?: string;
  activeModelKey?: string;
  onModelSelect: (modelKey: string) => void;
  onSetAsDefault?: () => void;
  isSettingDefault?: boolean;
  isCurrentModelDefault?: boolean;

  // MCP tool selection
  mcpServers?: McpServer[];
  selectedTools: McpToolSelection[];
  onToolsChange: (tools: McpToolSelection[]) => void;
}

/**
 * Chat controls component
 * Aggregates model selector and MCP tool selector
 */
export function ChatControls({
  models,
  selectedModelKey,
  activeModelKey,
  onModelSelect,
  onSetAsDefault,
  isSettingDefault = false,
  isCurrentModelDefault = false,
  mcpServers,
  selectedTools,
  onToolsChange,
}: ChatControlsProps) {
  return (
    <div className="grid gap-3 md:grid-cols-2">
      {/* Model Selector */}
      <ModelSelector
        models={models}
        selectedModelKey={selectedModelKey}
        activeModelKey={activeModelKey}
        onSelect={onModelSelect}
        onSetAsDefault={onSetAsDefault}
        isPending={isSettingDefault}
        isCurrentModelDefault={isCurrentModelDefault}
      />

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
