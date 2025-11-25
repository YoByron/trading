# Agent Usage Analysis: Active vs Sleeper Agents

**Date**: 2025-11-25  
**Status**: ⚠️ **NOT ALL AGENTS ACTIVE**

---

## 🎯 EXECUTIVE SUMMARY

**Current Reality**: We have **multiple agent systems**, but **NOT all are active** in the main execution path.

**Active Agents**:
- ✅ **DeepAgents** (enabled by default)
- ✅ **Langchain** (validation gate)
- ✅ **Gemini** (Tier 2 validation)
- ✅ **Python Rule-Based** (fallback)

**Sleeper Agents**:
- ❌ **Elite Orchestrator** (disabled by default - `ELITE_ORCHESTRATOR_ENABLED=false`)
- ❌ **Go ADK** (only used if Elite enabled)
- ❌ **MCP Orchestrator** (only used if Elite enabled)
- ❌ **Gemini3LangGraphAgent** (exists but unused)
- ❌ **Advanced Autonomous Trader** (separate script, not integrated)

---

## 📊 DETAILED BREAKDOWN

### ✅ ACTIVE AGENTS

#### 1. **DeepAgents** (`src/orchestration/deepagents_trading.py`)
**Status**: ✅ **ACTIVE** (enabled by default)

**Usage**:
```python
# scripts/autonomous_trader.py line 1344-1368
deepagents_enabled = os.getenv("DEEPAGENTS_ENABLED", "true").lower() == "true"
if deepagents_enabled:
    orchestrator = DeepAgentsTradingOrchestrator(symbols=symbols, paper=True)
    result = asyncio.run(orchestrator.execute_trading_cycle())
```

**What It Does**:
- Planning-based agent with sub-agent delegation
- Research → Signal → Risk → Execution workflow
- Uses Claude Skills internally

**Impact**: **HIGH** - Primary intelligent system in main execution path

---

#### 2. **Langchain Agents** (`langchain_agents/agents.py`)
**Status**: ✅ **ACTIVE** (validation gate)

**Usage**:
```python
# scripts/autonomous_trader.py - Tier 1 & Tier 2 validation
if langchain_enabled and langchain_agent:
    approved = langchain_agent.invoke({"input": f"ADK recommends {symbol}..."})
    if approved:
        execute_trade()
```

**What It Does**:
- Secondary approval gate after ADK/DeepAgents decisions
- Sentiment RAG queries
- MCP tool bridge (if enabled)

**Impact**: **MEDIUM** - Validation layer, improves decision quality

---

#### 3. **Gemini Agent** (`src/agents/gemini_agent.py`)
**Status**: ✅ **ACTIVE** (Tier 2 validation)

**Usage**:
```python
# scripts/autonomous_trader.py line 974-1006
if gemini_enabled and gemini_agent:
    gemini_result = gemini_agent.reason(
        prompt=gemini_prompt,
        thinking_level="high"
    )
    if "APPROVE" in decision:
        execute_trade()
```

**What It Does**:
- Strategic validation for Growth Strategy (Tier 2)
- Long-horizon planning
- High thinking level analysis

**Impact**: **MEDIUM** - Strategic validation for growth trades

---

#### 4. **Python Rule-Based Strategies**
**Status**: ✅ **ACTIVE** (fallback/primary)

**Usage**:
```python
# scripts/autonomous_trader.py
execute_tier1(daily_amount, risk_manager, account)  # Core Strategy
execute_tier2(daily_amount, risk_manager, account)  # Growth Strategy
```

**What It Does**:
- MACD + RSI + Volume technical analysis
- Rule-based position sizing
- Direct Alpaca API execution

**Impact**: **HIGH** - Fallback when intelligent agents unavailable

---

### ❌ SLEEPER AGENTS

#### 1. **Elite Orchestrator** (`src/orchestration/elite_orchestrator.py`)
**Status**: ❌ **DISABLED BY DEFAULT**

**Why It's Sleeper**:
```python
# src/main.py line 176
elite_enabled = os.getenv("ELITE_ORCHESTRATOR_ENABLED", "false").lower() == "true"
```

**What It Would Do**:
- Combines ALL agent frameworks:
  - Claude Skills (core flows)
  - Langchain (RAG, multi-modal)
  - Gemini (research, planning)
  - Go ADK (high-speed execution)
  - MCP Orchestrator (multi-agent)
  - ML Predictor (LSTM-PPO)
- Planning-first approach with 6 phases
- Ensemble voting across all agents

**How to Enable**:
```bash
export ELITE_ORCHESTRATOR_ENABLED=true
```

**Impact**: **VERY HIGH** - Would unify all agents into single intelligent system

---

#### 2. **Go ADK Orchestrator** (`go/adk_trading/`)
**Status**: ❌ **SLEEPER** (only used if Elite enabled)

**Why It's Sleeper**:
- Only initialized in `EliteOrchestrator._initialize_agents()`
- Elite Orchestrator is disabled by default
- Not used in `autonomous_trader.py` main path

**What It Would Do**:
- Multi-agent system: Research → Signal → Risk → Execution
- Uses Gemini 2.5 Flash model
- High-speed execution via Go runtime
- Structured JSON decisions with confidence scores

**Impact**: **HIGH** - High-speed execution layer (if enabled)

---

#### 3. **MCP Orchestrator** (`src/orchestration/mcp_trading.py`)
**Status**: ❌ **SLEEPER** (only used if Elite enabled)

**Why It's Sleeper**:
- Only initialized in `EliteOrchestrator._initialize_agents()`
- Elite Orchestrator is disabled by default

**What It Would Do**:
- Multi-agent coordination via MCP protocol
- Tool integration
- Fallback execution if ADK unavailable

**Impact**: **MEDIUM** - Multi-agent coordination layer

---

#### 4. **Gemini3LangGraphAgent** (`src/agents/gemini3_langgraph_agent.py`)
**Status**: ❌ **SLEEPER** (exists but unused)

**Why It's Sleeper**:
- Created but never called in main execution paths
- Separate from `GeminiAgent` which IS used
- No integration in `autonomous_trader.py` or `main.py`

**What It Would Do**:
- LangGraph-based multi-agent workflow
- Research → Analysis → Decision pipeline
- Multi-modal analysis support

**Impact**: **LOW** - Redundant with existing GeminiAgent

---

#### 5. **Advanced Autonomous Trader** (`scripts/advanced_autonomous_trader.py`)
**Status**: ❌ **SLEEPER** (separate script, not integrated)

**Why It's Sleeper**:
- Separate script, not called by main execution
- Uses MetaAgent + ResearchAgent + SignalAgent + RiskAgent + ExecutionAgent
- Not integrated into CI/CD or main orchestrator

**What It Would Do**:
- Multi-agent coordination with RL learner
- Meta-agent pattern
- Sub-agent delegation

**Impact**: **MEDIUM** - Alternative architecture, not currently used

---

## 🔄 CURRENT EXECUTION FLOW

### Main Path (`scripts/autonomous_trader.py`)

```
1. Check DeepAgents (enabled by default)
   └─> DeepAgentsTradingOrchestrator.execute_trading_cycle()
       └─> Planning → Research → Signal → Risk → Execute

2. If DeepAgents fails/skips:
   └─> Execute Tier 1 (Core Strategy)
       └─> Langchain validation (if enabled)
       └─> Execute trade

3. Execute Tier 2 (Growth Strategy)
   └─> Gemini validation (if enabled)
   └─> Langchain validation (if enabled)
   └─> Execute trade
```

### Alternative Path (`src/main.py` - TradingOrchestrator)

```
1. Check Elite Orchestrator (DISABLED by default)
   └─> EliteOrchestrator.run_trading_cycle()
       └─> All agents unified

2. Check DeepAgents
   └─> DeepAgentsTradingOrchestrator

3. Check ADK
   └─> ADKTradeAdapter

4. Fallback to Python Rule-Based
   └─> CoreStrategy.execute_daily()
```

---

## 🚀 RECOMMENDATIONS

### Option 1: Enable Elite Orchestrator (Recommended)
**Unifies all agents into single intelligent system**

```bash
# Enable in .env or GitHub Secrets
ELITE_ORCHESTRATOR_ENABLED=true
```

**Benefits**:
- ✅ Uses ALL agent systems together
- ✅ Ensemble voting across agents
- ✅ Planning-first approach
- ✅ Better decision quality

**Risks**:
- ⚠️ More complex, harder to debug
- ⚠️ Requires all dependencies configured

---

### Option 2: Keep Current Architecture
**Simpler, more reliable**

**Benefits**:
- ✅ Simpler execution path
- ✅ Easier to debug
- ✅ DeepAgents + Langchain + Gemini working well

**Drawbacks**:
- ❌ Not using Go ADK (high-speed execution)
- ❌ Not using MCP Orchestrator (multi-agent coordination)
- ❌ Not using unified ensemble voting

---

### Option 3: Hybrid Approach
**Enable Elite Orchestrator for Tier 1, keep current for Tier 2**

```python
# In autonomous_trader.py
if tier == "Tier1":
    # Use Elite Orchestrator (all agents)
    elite_result = elite_orchestrator.run_trading_cycle()
else:
    # Use current DeepAgents + validation
    deepagents_result = deepagents_orchestrator.execute_trading_cycle()
```

---

## 📋 AGENT INVENTORY SUMMARY

| Agent System | Status | Usage | Impact if Enabled |
|-------------|--------|-------|-------------------|
| **DeepAgents** | ✅ Active | Primary intelligent system | N/A (already active) |
| **Langchain** | ✅ Active | Validation gate | N/A (already active) |
| **Gemini** | ✅ Active | Tier 2 validation | N/A (already active) |
| **Python Rules** | ✅ Active | Fallback/primary | N/A (already active) |
| **Elite Orchestrator** | ❌ Sleeper | Disabled by default | **VERY HIGH** - Unifies all |
| **Go ADK** | ❌ Sleeper | Only if Elite enabled | **HIGH** - High-speed execution |
| **MCP Orchestrator** | ❌ Sleeper | Only if Elite enabled | **MEDIUM** - Multi-agent coordination |
| **Gemini3LangGraph** | ❌ Sleeper | Never used | **LOW** - Redundant |
| **Advanced Trader** | ❌ Sleeper | Separate script | **MEDIUM** - Alternative architecture |

---

## 🎯 CONCLUSION

**Answer**: **NO, not all agents are active**. The Elite Orchestrator (which combines Claude Skills, Langchain, Gemini, Go ADK, MCP) is **disabled by default**.

**Current State**:
- ✅ DeepAgents + Langchain + Gemini + Python Rules = **ACTIVE**
- ❌ Elite Orchestrator + Go ADK + MCP = **SLEEPER**

**To Use All Agents**: Enable `ELITE_ORCHESTRATOR_ENABLED=true`

