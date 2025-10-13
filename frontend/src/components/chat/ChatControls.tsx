"use client";

import { ModelSelector } from "@/components/ui/ModelSelector";
import { MCPToolSelector } from "@/components/ui/MCPToolSelector";
import { PromptSelector, ToolsSelector } from "@/features/agno";
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

  // MCP tool selection
  mcpServers?: McpServer[];
  selectedTools: McpToolSelection[];
  onToolsChange: (tools: McpToolSelection[]) => void;

  // Agno configuration
  promptKey?: string;
  onPromptKeyChange: (promptKey: string | undefined) => void;
  selectedAgnoTools: string[];
  onAgnoToolsChange: (tools: string[]) => void;
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
  mcpServers,
  selectedTools,
  onToolsChange,
  promptKey,
  onPromptKeyChange,
  selectedAgnoTools,
  onAgnoToolsChange,
}: ChatControlsProps) {
  return (
    <div className="space-y-3">
      {/* First row: Model and MCP Tools */}
      <div className="grid gap-3 md:grid-cols-2">
        {/* Model Selector */}
        <ModelSelector
          models={models}
          selectedModelKey={selectedModelKey}
          activeModelKey={activeModelKey}
          onSelect={onModelSelect}
          onSetAsDefault={onSetAsDefault}
          isPending={isSettingDefault}
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

      {/* Second row: Agno Prompt and Tools */}
      <div className="grid gap-3 md:grid-cols-2">
        {/* Prompt Selector */}
        <PromptSelector
          value={promptKey}
          onChange={onPromptKeyChange}
          className=""
        />

        {/* Agno Tools Selector */}
        <ToolsSelector
          value={selectedAgnoTools}
          onChange={onAgnoToolsChange}
          className=""
        />
      </div>
    </div>
  );
}
