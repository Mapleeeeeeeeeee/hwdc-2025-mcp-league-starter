# Agno Tools and Prompts - Frontend Integration

## Overview

This document describes how to use the Agno tools and prompts feature in the frontend.

## Components

### 1. PromptSelector

A dropdown selector for choosing prompt presets.

```tsx
import { PromptSelector } from "@/features/agno";

function MyComponent() {
  const [promptKey, setPromptKey] = useState<string | undefined>();

  return (
    <PromptSelector
      value={promptKey}
      onChange={setPromptKey}
      className="mb-4"
    />
  );
}
```

### 2. ToolsSelector

A checkbox list for selecting which Agno tools to use.

```tsx
import { ToolsSelector } from "@/features/agno";

function MyComponent() {
  const [selectedTools, setSelectedTools] = useState<string[]>([]);

  return (
    <ToolsSelector
      value={selectedTools}
      onChange={setSelectedTools}
      className="mb-4"
    />
  );
}
```

## Hooks

### useAgnoConfig

Fetch the current Agno configuration (toolkits and prompts).

```tsx
import { useAgnoConfig } from "@/features/agno";

function MyComponent() {
  const { data, isLoading, error } = useAgnoConfig();

  if (isLoading) return <div>Loading...</div>;
  if (error) return <div>Error: {String(error)}</div>;

  return (
    <div>
      <h3>Available Tools:</h3>
      <ul>
        {data?.toolkits.map((toolkit) => (
          <li key={toolkit.key}>
            {toolkit.key} - {toolkit.enabled ? "Enabled" : "Disabled"}
          </li>
        ))}
      </ul>
    </div>
  );
}
```

### useUpdateToolkit

Update a toolkit's enabled status.

```tsx
import { useUpdateToolkit } from "@/features/agno";

function MyComponent() {
  const updateToolkit = useUpdateToolkit();

  const handleToggle = () => {
    updateToolkit.mutate({ key: "duckduckgo_search", enabled: false });
  };

  return <button onClick={handleToggle}>Disable DuckDuckGo</button>;
}
```

### useUpdatePrompt

Update a prompt's enabled status.

```tsx
import { useUpdatePrompt } from "@/features/agno";

function MyComponent() {
  const updatePrompt = useUpdatePrompt();

  const handleToggle = () => {
    updatePrompt.mutate({ key: "analytical", enabled: true });
  };

  return <button onClick={handleToggle}>Enable Analytical Prompt</button>;
}
```

## Utility Functions

### enhanceMessageWithToolHints

Add tool usage hints to user messages.

```tsx
import { enhanceMessageWithToolHints } from "@/features/agno";

const originalMessage = "What is the latest SpaceX news?";
const selectedTools = ["duckduckgo_search"];

const enhancedMessage = enhanceMessageWithToolHints(
  originalMessage,
  selectedTools,
);

// Result: "What is the latest SpaceX news?\n\nPlease use duckduckgo search to help answer this question."
```

## Integration with Conversation

To integrate Agno tools and prompts into your chat interface:

```tsx
import { useState } from "react";
import {
  PromptSelector,
  ToolsSelector,
  enhanceMessageWithToolHints,
} from "@/features/agno";
import { useConversationMutation } from "@/features/conversation";

function ChatInterface() {
  const [promptKey, setPromptKey] = useState<string | undefined>();
  const [selectedTools, setSelectedTools] = useState<string[]>([]);
  const [userMessage, setUserMessage] = useState("");

  const sendMessage = useConversationMutation();

  const handleSend = async () => {
    // Enhance message with tool hints
    const enhancedMessage = enhanceMessageWithToolHints(
      userMessage,
      selectedTools,
    );

    await sendMessage.mutateAsync({
      conversationId: "my-conversation",
      history: [{ role: "user", content: enhancedMessage }],
      promptKey, // Pass selected prompt
      modelKey: "openai:gpt-5-mini",
      tools: [], // Empty to exclude MCP tools
    });
  };

  return (
    <div>
      {/* Prompt selector */}
      <PromptSelector value={promptKey} onChange={setPromptKey} />

      {/* Tools selector */}
      <ToolsSelector value={selectedTools} onChange={setSelectedTools} />

      {/* Message input */}
      <input
        value={userMessage}
        onChange={(e) => setUserMessage(e.target.value)}
        placeholder="Type your message..."
      />

      <button onClick={handleSend}>Send</button>
    </div>
  );
}
```

## How It Works

1. **Agno Tools (Auto-loaded)**:
   - All enabled tools are automatically loaded when an agent is created
   - Tools are always available to the agent
   - Selected tools in the UI add natural language hints to guide the agent

2. **Natural Language Hints**:
   - When a tool is selected, a hint is added to the user's message
   - Example: "Please use duckduckgo search to help answer this question."
   - This encourages the agent to use the selected tool

3. **Prompts**:
   - The `promptKey` parameter controls which prompt preset is used
   - Different prompts change the agent's behavior (analytical, creative, etc.)
   - If not specified, the "default" prompt is used

## Testing

Run tests for the Agno feature:

```bash
pnpm test src/features/agno
```

## API Endpoints

The frontend uses these backend endpoints:

- `GET /api/v1/agno/config` - Get all toolkits and prompts
- `PATCH /api/v1/agno/toolkits/{key}` - Enable/disable a toolkit
- `PATCH /api/v1/agno/prompts/{key}` - Enable/disable a prompt
