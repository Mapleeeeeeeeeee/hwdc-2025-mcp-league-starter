# Agno Tools and Prompts Integration

這個文檔說明如何在當前設計中使用 Tools 和 Prompts 配置。

## 架構設計

### 配置文件結構

1. **llm_models.json** - 定義 LLM 模型配置（provider, model_id, API key 等）
2. **agno_tools.json** - 定義 Agent 可用的工具配置
3. **agno_prompts.json** - 定義 Agent 的提示詞預設配置

這三個配置文件**各司其職**：
- `llm_models.json`: 模型本身的設定
- `agno_tools.json`: Agent 的能力（工具）
- `agno_prompts.json`: Agent 的行為指令

## 配置示例

### agno_tools.json

```json
{
  "toolkits": [
    {
      "key": "duckduckgo_search",
      "toolkit_class": "agno.tools.duckduckgo.DuckDuckGoTools",
      "enabled": true,
      "config": {}
    },
    {
      "key": "reasoning",
      "toolkit_class": "agno.tools.reasoning.ReasoningTools",
      "enabled": true,
      "config": {
        "think": true,
        "analyze": true,
        "add_instructions": true,
        "add_few_shot": true
      }
    }
  ]
}
```

### agno_prompts.json

```json
{
  "prompts": [
    {
      "key": "default",
      "name": "Default Instructions",
      "enabled": true,
      "instructions": [
        "You are a helpful AI assistant.",
        "Always be clear and concise in your responses."
      ]
    },
    {
      "key": "analytical",
      "name": "Analytical Assistant",
      "enabled": false,
      "instructions": [
        "Think step by step before answering.",
        "Use tables where possible to organize information."
      ]
    }
  ]
}
```

## Python 使用方式

### 基本使用

```python
from src.integrations.llm import ConversationAgentFactory

# 創建 factory（會自動加載配置）
factory = ConversationAgentFactory()

# 創建帶有工具和提示詞的 Agent
agent = factory.create_agent(
    model_key="openai:gpt-4o-mini",  # 從 llm_models.json
    prompt_key="default",             # 從 agno_prompts.json
)

# Agent 會自動具備以下功能：
# 1. 使用 OpenAI GPT-4o-mini 模型
# 2. 具備 DuckDuckGo 搜索和 Reasoning 工具
# 3. 遵循 "default" 提示詞的指令
```

### 查詢可用配置

```python
# 查看所有可用模型
models = factory.get_available_models()

# 查看所有可用提示詞預設
prompts = factory.get_available_prompts()

# 查看啟用的工具
tools = factory.get_enabled_tools()
```

## 動態工具加載

ToolsConfigStore 會根據配置**動態加載**工具類：

```python
# agno_tools.json 中的配置
{
  "key": "duckduckgo_search",
  "toolkit_class": "agno.tools.duckduckgo.DuckDuckGoTools",
  "config": {}
}

# 會被轉換為
from agno.tools.duckduckgo import DuckDuckGoTools
tool_instance = DuckDuckGoTools()
```

## 可用的 Agno 工具

根據 Agno 文檔，以下是一些常用工具：

### 搜索工具
- `agno.tools.duckduckgo.DuckDuckGoTools` - DuckDuckGo 搜索
- `agno.tools.tavily.TavilyTools` - Tavily 搜索

### 推理工具
- `agno.tools.reasoning.ReasoningTools` - 增強推理能力
- `agno.tools.memory.MemoryTools` - 記憶管理
- `agno.tools.knowledge.KnowledgeTools` - 知識庫工具

### 數據工具
- `agno.tools.yfinance.YFinanceTools` - 金融數據
- `agno.tools.googlesheets.GoogleSheetsTools` - Google Sheets

### 社交工具
- `agno.tools.slack.SlackTools` - Slack 整合
- `agno.tools.discord.DiscordTools` - Discord 整合
- `agno.tools.reddit.RedditTools` - Reddit 整合

### AWS 工具
- `agno.tools.aws_ses.AWSSESTool` - AWS SES 郵件
- `agno.tools.aws_lambda.AWSLambdaTool` - AWS Lambda

## 自定義工具

你也可以定義自己的工具並加入配置：

```python
# 在 src/integrations/llm/custom_tools.py 中定義
from agno.tools import tool

@tool
def get_weather(city: str) -> str:
    """Get weather for a city."""
    return f"Weather in {city}: Sunny"
```

然後在 `agno_tools.json` 中添加：

```json
{
  "custom_tools": [
    {
      "key": "weather",
      "module_path": "src.integrations.llm.custom_tools",
      "function_name": "get_weather",
      "enabled": true
    }
  ]
}
```

## 優勢

1. **分離關注點**：模型、工具、提示詞各自獨立配置
2. **動態加載**：修改配置文件即可改變 Agent 能力，無需修改代碼
3. **可擴展**：輕鬆添加新工具或提示詞預設
4. **類型安全**：使用 Pydantic 模型驗證配置
5. **靈活組合**：可以為不同場景創建不同的 Agent 配置

## 與現有 API 整合

在 MCP Server 或 REST API 中使用：

```python
# 在 API endpoint 中
agent_factory = ConversationAgentFactory()

# 用戶可以選擇不同的提示詞模式
agent = agent_factory.create_agent(
    model_key=request.model_key,
    prompt_key=request.prompt_mode,  # "default", "analytical", "creative" 等
)

response = agent.print_response(request.message)
```
