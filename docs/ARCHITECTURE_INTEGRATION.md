# 🏗️ Architecture: Go ADK + Langchain + Python Integration

**Last Updated**: November 12, 2025  
**Status**: ADK Currently DISABLED (R&D Phase)  
**Integration**: Complete but dormant

---

## 📊 OVERVIEW

Your trading system has **three agent frameworks** that can work together:

1. **Go ADK Agents** (Google Agent Development Kit) - Multi-agent orchestrator in Go
2. **Langchain Agents** (Python) - Price-action analysis with sentiment RAG
3. **Python Strategies** (CoreStrategy/GrowthStrategy) - Rule-based momentum trading

**Current State**: ADK is **DISABLED** during R&D Phase (Days 1-90) per PLAN.md decision.

---

## 🔄 HOW THEY INTEGRATE

### Architecture Flow

```
┌─────────────────────────────────────────────────────────────┐
│                    PYTHON TRADING STACK                      │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  CoreStrategy / GrowthStrategy                       │  │
│  │  (Rule-based: MACD + RSI + Volume)                   │  │
│  │                                                       │  │
│  │  ┌─────────────────────────────────────────────┐    │  │
│  │  │  ADKTradeAdapter.evaluate()                 │    │  │
│  │  │  (Optional: Calls Go ADK if enabled)        │    │  │
│  │  └─────────────────────────────────────────────┘    │  │
│  └──────────────────────────────────────────────────────┘  │
│                          │                                  │
│                          │ HTTP REST API                    │
│                          ▼                                  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Go ADK Orchestrator Service                         │  │
│  │  (http://127.0.0.1:8080/api)                        │  │
│  │                                                       │  │
│  │  Root Agent → Coordinates 4 sub-agents:              │  │
│  │    • Research Agent (market data analysis)          │  │
│  │    • Signal Agent (trade idea generation)           │  │
│  │    • Risk Agent (position sizing, validation)        │  │
│  │    • Execution Agent (plan logging)                  │  │
│  └──────────────────────────────────────────────────────┘  │
│                          │                                  │
│                          │ Context (includes RAG sentiment) │
│                          ▼                                  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Langchain Agents (Python)                           │  │
│  │  • Price-action analyst                             │  │
│  │  • Sentiment RAG queries                            │  │
│  │  • MCP tool bridge                                  │  │
│  └──────────────────────────────────────────────────────┘  │
│                          │                                  │
│                          │ Sentiment Data                   │
│                          ▼                                  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Sentiment RAG Store (SQLite)                        │  │
│  │  • Reddit sentiment                                 │  │
│  │  • News sentiment                                   │  │
│  │  • Historical snapshots                             │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

---

## 🔌 INTEGRATION POINTS

### 1. Python → Go ADK (HTTP REST API)

**Location**: `src/orchestration/adk_client.py` + `src/orchestration/adk_integration.py`

**How it works**:
```python
# Python Strategy calls ADK adapter
adk_adapter = ADKTradeAdapter(enabled=True)

# Evaluate symbols through Go ADK orchestrator
decision = adk_adapter.evaluate(
    symbols=["SPY", "QQQ", "VOO"],
    context={
        "mode": "paper",
        "rag_sentiment": {...}  # Enriched with sentiment data
    }
)

# ADK returns structured decision
if decision and decision.action == "BUY":
    # Execute trade based on ADK recommendation
    execute_order(decision.symbol, decision.position_size)
```

**HTTP Request Flow**:
1. Python → `POST http://127.0.0.1:8080/api/run`
2. Go ADK orchestrator processes through 4 agents
3. Returns JSON with trade decision
4. Python parses and executes (or falls back to rule-based)

---

### 2. Go ADK → Langchain (Sentiment Context)

**Location**: `src/orchestration/adk_integration.py` → `_load_sentiment()`

**How it works**:
```python
# ADK adapter enriches context with sentiment BEFORE calling Go
enriched_ctx = {
    **context_base,
    "rag_sentiment": self._load_sentiment(symbol),  # From SQLite RAG store
}

# Sentiment includes:
{
    "samples": [...],           # Recent sentiment snapshots
    "average_score": 0.65,      # Average sentiment score
    "latest_score": 0.72,       # Most recent score
    "confidence_mode": "HIGH",  # Confidence level
    "market_regime": "BULLISH"  # Market regime
}

# This enriched context is sent to Go ADK orchestrator
result = self.client.run_structured(
    symbol=symbol,
    context=enriched_ctx,  # Includes Langchain-accessible sentiment
)
```

**Data Flow**:
1. Langchain agents query sentiment RAG store
2. Sentiment data stored in SQLite (`rag_store/`)
3. ADK adapter loads sentiment for symbol
4. Enriches context sent to Go ADK orchestrator
5. Go agents use sentiment in decision-making

---

### 3. Langchain → MCP Tools (Brokerage Access)

**Location**: `langchain_agents/toolkit.py` → `build_mcp_tool()`

**How it works**:
```python
# Langchain agent can call MCP tools (including Alpaca trading)
agent = build_price_action_agent()

# Agent can invoke MCP tools via Langchain
result = agent.invoke({
    "input": "Get latest bars for SPY and check account balance"
})

# Langchain calls MCP tool bridge
mcp_tool_call(
    server="alpaca",
    tool="get_latest_bars",
    payload={"symbols": ["SPY"], "limit": 200}
)
```

**MCP Bridge**:
- Langchain agents → MCP client → Alpaca MCP server → Alpaca API
- Provides Langchain agents access to trading capabilities
- Can be enabled/disabled via `LANGCHAIN_ENABLE_MCP` env var

---

## 📁 KEY FILES

### Go ADK Orchestrator
- **Main**: `go/adk_trading/cmd/trading_orchestrator/main.go`
- **Agents**: `go/adk_trading/internal/agents/agents.go`
- **Tools**: `go/adk_trading/internal/tools/` (marketdata, risk, logging)

### Python Integration
- **Client**: `src/orchestration/adk_client.py` (HTTP client for Go ADK)
- **Adapter**: `src/orchestration/adk_integration.py` (RAG enrichment wrapper)
- **Strategy**: `src/strategies/core_strategy.py` (calls ADK adapter)

### Langchain Agents
- **Agents**: `langchain_agents/agents.py` (price-action analyst)
- **Tools**: `langchain_agents/toolkit.py` (sentiment RAG + MCP bridge)
- **Playbooks**: `langchain_agents/playbooks/price_action_analyst.py`

---

## 🎯 CURRENT USAGE

### Active (R&D Phase)
- ✅ **Python Strategies**: CoreStrategy + GrowthStrategy (rule-based)
- ✅ **Langchain Agents**: Sentiment RAG queries (via toolkit)
- ❌ **Go ADK**: DISABLED (per PLAN.md decision)

### Why ADK is Disabled
From `docs/PLAN.md`:
> **Decision**: Keep ADK DISABLED during R&D Phase (Days 1-90)  
> **Rationale**: Focus on proving trading edge with simple, reliable Python execution first  
> **Future**: Enable in Month 4+ IF Python system proves profitable

---

## 🚀 HOW TO ENABLE ADK

### Step 1: Start Go ADK Service
```bash
cd go/adk_trading
go run cmd/trading_orchestrator/main.go \
  -model gemini-2.5-flash \
  -data_dir ../data \
  -log_path ../logs/adk_orchestrator.jsonl
```

### Step 2: Set Environment Variables
```bash
export ADK_ENABLED=1
export ADK_BASE_URL=http://127.0.0.1:8080/api
export ADK_APP_NAME=trading_orchestrator
export GOOGLE_API_KEY=your_gemini_api_key
```

### Step 3: Python Strategy Will Use ADK
```python
# In CoreStrategy.execute_daily()
if self.adk_adapter.enabled:
    decision = self.adk_adapter.evaluate(symbols=["SPY", "QQQ", "VOO"])
    if decision and decision.action == "BUY":
        # Use ADK decision instead of rule-based
        return execute_order(decision.symbol, decision.position_size)

# Fallback to rule-based if ADK disabled or fails
return self._execute_rule_based()
```

---

## 🔄 DECISION FLOW (When ADK Enabled)

```
1. CoreStrategy.execute_daily() called
   │
   ├─► Try ADK adapter first (if enabled)
   │   │
   │   ├─► ADK adapter loads sentiment from RAG store
   │   │   │
   │   │   └─► Sentiment data enriched with Langchain queries
   │   │
   │   ├─► HTTP POST to Go ADK orchestrator
   │   │   │
   │   │   ├─► Research Agent: Analyzes market data
   │   │   ├─► Signal Agent: Generates trade idea
   │   │   ├─► Risk Agent: Validates position size
   │   │   └─► Execution Agent: Logs plan
   │   │
   │   └─► Returns ADKDecision (symbol, action, confidence, position_size)
   │
   └─► Fallback to rule-based (MACD + RSI + Volume) if ADK disabled/fails
```

---

## 🛠️ TECHNICAL DETAILS

### Go ADK Agents Architecture

**Root Agent** (`trading_orchestrator_root_agent`):
- Coordinates 4 sub-agents
- Returns structured JSON decision

**Sub-Agents**:
1. **Research Agent**: Uses `marketdata` tool to analyze symbol
2. **Signal Agent**: Generates trade signals using market data
3. **Risk Agent**: Uses `risk` tool to validate position sizing
4. **Execution Agent**: Uses `logging` tool to record plan

**Tools** (Go):
- `marketdata`: Fetches OHLCV data from data directory
- `risk`: Calculates position sizes, validates risk limits
- `logging`: Records execution plans to JSONL

### Langchain Agents Architecture

**Price-Action Agent**:
- Uses Claude (Anthropic) as LLM
- Tools: Sentiment RAG queries + MCP tool bridge
- Purpose: Qualitative market analysis

**Sentiment Tools**:
- `query_sentiment_context`: Semantic search over sentiment history
- `get_recent_sentiment_history`: Fetch latest sentiment for ticker

**MCP Bridge**:
- Allows Langchain agents to call MCP servers
- Can access Alpaca trading, market data, etc.

### Python Strategy Integration

**ADKTradeAdapter**:
- Wraps `ADKOrchestratorClient` with RAG enrichment
- Loads sentiment from SQLite before calling Go ADK
- Selects best decision across multiple symbols

**Fallback Logic**:
- If ADK disabled → Use rule-based strategy
- If ADK fails → Use rule-based strategy
- If ADK returns no decision → Use rule-based strategy

---

## 📊 DATA FLOW EXAMPLE

### Scenario: Trading SPY

1. **Python Strategy** calls `adk_adapter.evaluate(["SPY"])`

2. **ADK Adapter** enriches context:
   ```python
   context = {
       "mode": "paper",
       "rag_sentiment": {
           "average_score": 0.68,
           "latest_score": 0.72,
           "market_regime": "BULLISH",
           "samples": [...]  # From Langchain-accessible RAG store
       }
   }
   ```

3. **HTTP Request** to Go ADK:
   ```http
   POST http://127.0.0.1:8080/api/run
   {
     "appName": "trading_orchestrator",
     "userId": "python-stack",
     "sessionId": "spy-1234567890-abc123",
     "newMessage": {
       "role": "user",
       "parts": [{
         "text": "Run the ADK trading orchestrator end-to-end for symbol SPY.\nContext JSON:\n{...}"
       }]
     }
   }
   ```

4. **Go ADK Orchestrator** processes:
   - Research Agent → Analyzes SPY market data
   - Signal Agent → Generates BUY signal (confidence: 0.75)
   - Risk Agent → Validates position size ($6,000)
   - Execution Agent → Logs execution plan

5. **Go ADK Returns** JSON:
   ```json
   {
     "symbol": "SPY",
     "trade_summary": {
       "action": "BUY",
       "confidence": 0.75
     },
     "risk": {
       "decision": "APPROVE",
       "position_size": 6000.0
     },
     "execution": {...},
     "sentiment": {...}
   }
   ```

6. **Python Strategy** executes:
   ```python
   if decision.action == "BUY":
       execute_order("SPY", 6000.0)
   ```

---

## ⚙️ CONFIGURATION

### Environment Variables

**ADK Service**:
- `ADK_ENABLED`: Enable/disable ADK integration (default: 0)
- `ADK_BASE_URL`: Go ADK service URL (default: http://127.0.0.1:8080/api)
- `ADK_APP_NAME`: App name (default: trading_orchestrator)
- `ADK_ROOT_AGENT`: Root agent name (default: trading_orchestrator_root_agent)
- `GOOGLE_API_KEY`: Gemini API key (required for Go ADK)

**Langchain**:
- `LANGCHAIN_MODEL`: Model name (default: claude-3-5-sonnet-20241022)
- `LANGCHAIN_TEMPERATURE`: Temperature (default: 0.3)
- `LANGCHAIN_ENABLE_MCP`: Enable MCP tool bridge (default: true)

---

## 🎯 SUMMARY

**Current State**:
- ✅ Go ADK orchestrator: Built and ready (but disabled)
- ✅ Langchain agents: Active for sentiment analysis
- ✅ Python strategies: Active (rule-based, no ADK)
- ✅ Integration code: Complete and tested

**Integration Points**:
1. Python → Go ADK: HTTP REST API (`adk_client.py`)
2. Go ADK ← Langchain: Sentiment context enrichment (`adk_integration.py`)
3. Langchain → MCP: Tool bridge for brokerage access (`toolkit.py`)

**When ADK Enabled**:
- Python strategies call Go ADK orchestrator first
- Go ADK uses sentiment data from Langchain-accessible RAG store
- Falls back to rule-based if ADK disabled/fails

**Decision**: Keep ADK disabled during R&D Phase (Days 1-90) per PLAN.md. Enable in Month 4+ if Python system proves profitable.

---

## 📚 RELATED DOCS

- `docs/PLAN.md` - ADK architectural decision
- `docs/ADK_DEPLOYMENT_PLAYBOOK.md` - How to deploy ADK
- `docs/ADK_TRADING_QUICKSTART.md` - Quick start guide
- `docs/CLAUDE_AGENT_SDK_LOOP.md` - Agent SDK patterns

