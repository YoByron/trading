# Context Engineering for Multi-Agent Trading Systems

**Last Updated**: November 26, 2025
**Status**: ✅ Integrated

## Overview

This document describes the Context Engineering implementation in our multi-agent trading system, integrating principles from:

- **"Context Engineering for Multi-Agent Systems"** (Packt Publishing)
- **"Context Engineering for Multi-Agent LLM Code Assistants"** (arXiv:2508.08322)

## Key Concepts

### 1. Context Engineering vs Prompt Engineering

**Traditional Prompt Engineering:**
- Unstructured prompts passed to LLMs
- Context embedded directly in prompts
- No validation or structure
- Information loss between agents

**Context Engineering:**
- Structured semantic blueprints defining agent roles
- Explicit input/output schemas
- Validated context flow between agents
- Persistent context storage outside prompts
- Memory mechanisms for continuity

### 2. Semantic Blueprints

A **Semantic Blueprint** is a structured definition of an agent that includes:

- **Role**: What the agent does
- **Capabilities**: What it can do
- **Input Schema**: What it needs (with types and requirements)
- **Output Schema**: What it produces
- **Communication Protocol**: How it communicates (MCP format)
- **Dependencies**: Other agents it depends on
- **Context Window Size**: Estimated tokens needed

Example:
```python
research_blueprint = SemanticBlueprint(
    agent_id="research_agent",
    agent_name="Research Agent",
    role="Market Research Specialist",
    capabilities=["Fundamental analysis", "News sentiment", "Market regime detection"],
    inputs={
        "symbol": {"type": "string", "required": True},
        "timeframe": {"type": "string", "required": False, "default": "1Day"}
    },
    outputs={
        "market_regime": {"type": "string"},
        "sentiment_score": {"type": "float"},
        "confidence": {"type": "float"}
    },
    communication_protocol={"format": "MCP", "message_schema": "research_result"},
    dependencies=[]
)
```

### 3. Context Flow

Context flows between agents using structured **Context Messages**:

```python
message = context_engine.send_context_message(
    sender="research_agent",
    receiver="signal_agent",
    payload={"market_regime": "bullish", "sentiment_score": 0.75},
    context_type=ContextType.TASK_CONTEXT,
    metadata={"symbol": "AAPL"}
)
```

Messages are:
- Validated for structure and completeness
- Stored in message history
- Persisted to disk
- Convertible to MCP format

### 4. Context Validation

Before context flows between agents, the system validates:

1. **Both agents have blueprints**
2. **Sender's outputs match receiver's inputs**
3. **Required fields are present**

```python
is_valid, errors = context_engine.validate_context_flow(
    from_agent="research_agent",
    to_agent="signal_agent",
    context={"market_regime": "bullish", "sentiment_score": 0.75}
)
```

### 5. Memory & Persistence

The Context Engine provides:

- **Short-term memory**: Session-based, TTL-based expiration
- **Long-term memory**: Persistent storage
- **Tagged retrieval**: Find memories by agent ID and tags
- **Access tracking**: Track which memories are used most

```python
# Store memory
memory = context_engine.store_memory(
    agent_id="research_agent",
    content={"symbol": "AAPL", "sentiment": 0.75},
    tags={"AAPL", "sentiment", "research"},
    ttl_days=7  # Short-term memory
)

# Retrieve memories
memories = context_engine.retrieve_memories(
    agent_id="research_agent",
    tags={"AAPL"},
    limit=10
)
```

## Architecture

### Components

1. **Context Engine** (`src/agent_framework/context_engine.py`)
   - Core context management
   - Blueprint storage and retrieval
   - Message passing
   - Memory management
   - Validation

2. **Agent Blueprints** (`src/agent_framework/agent_blueprints.py`)
   - Semantic blueprints for all trading agents
   - Registration function

3. **Integration Points**:
   - `EliteOrchestrator`: Uses Context Engine for all phases
   - `MCPTradingOrchestrator`: Validates context flow
   - All agents: Can retrieve their context via blueprints

### Data Flow

```
┌─────────────────────────────────────────────────────────────┐
│                    Context Engine                            │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │  Blueprints  │  │   Messages   │  │   Memory     │     │
│  │   Storage    │  │   History    │  │   Storage    │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
└─────────────────────────────────────────────────────────────┘
         │                    │                    │
         ▼                    ▼                    ▼
┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
│  Research Agent │  │  Signal Agent   │  │  Risk Agent      │
│  (Blueprint)    │──│  (Blueprint)    │──│  (Blueprint)     │
│                 │  │                 │  │                  │
│  [Context]      │  │  [Context]      │  │  [Context]       │
└─────────────────┘  └─────────────────┘  └─────────────────┘
```

## Usage

### Initialization

The Context Engine is automatically initialized when orchestrators start:

```python
from src.agent_framework.context_engine import get_context_engine
from src.agent_framework import agent_blueprints

# Get context engine (singleton)
context_engine = get_context_engine()

# Register all agent blueprints
agent_blueprints.register_trading_agent_blueprints()
```

### Getting Agent Context

Retrieve complete context for an agent (blueprint + memories + recent messages):

```python
context = context_engine.get_agent_context("research_agent", max_tokens=8000)
# Returns: {
#   "blueprint": {...},
#   "memories": [...],
#   "recent_messages": [...]
# }
```

### Sending Context Messages

Send structured messages between agents:

```python
message = context_engine.send_context_message(
    sender="research_agent",
    receiver="signal_agent",
    payload={"market_regime": "bullish", "sentiment_score": 0.75},
    context_type=ContextType.TASK_CONTEXT,
    metadata={"symbol": "AAPL", "phase": "analysis"}
)
```

### Storing Memory

Store context for later retrieval:

```python
memory = context_engine.store_memory(
    agent_id="research_agent",
    content={
        "symbol": "AAPL",
        "sentiment": 0.75,
        "timestamp": "2025-11-26T10:00:00"
    },
    tags={"AAPL", "sentiment", "research"},
    ttl_days=7  # Expires in 7 days
)
```

### Validating Context Flow

Validate context before passing between agents:

```python
is_valid, errors = context_engine.validate_context_flow(
    from_agent="research_agent",
    to_agent="signal_agent",
    context={"market_regime": "bullish", "sentiment_score": 0.75}
)

if not is_valid:
    logger.warning(f"Context validation errors: {errors}")
```

## Registered Agents

All trading agents have semantic blueprints:

1. **research_agent**: Market Research Specialist
2. **signal_agent**: Trading Signal Generator
3. **risk_agent**: Risk Management Specialist
4. **execution_agent**: Trade Execution Specialist
5. **meta_agent**: Multi-Agent Coordinator
6. **gemini_agent**: Long-Horizon Research Specialist
7. **langchain_agent**: RAG and Multi-Modal Fusion Specialist

See `src/agent_framework/agent_blueprints.py` for complete definitions.

## Storage Structure

Context Engine stores data in `data/agent_context/`:

```
data/agent_context/
├── blueprints/
│   ├── research_agent.json
│   ├── signal_agent.json
│   ├── risk_agent.json
│   └── ...
├── memories/
│   ├── {memory_id}.json
│   └── ...
└── messages/
    ├── {message_id}.json
    └── ...
```

## Benefits

### 1. Structured Communication
- Agents communicate via validated, structured messages
- No information loss between agents
- Clear input/output contracts

### 2. Better Context Management
- Context stored outside prompts (reduces token usage)
- Persistent memory across sessions
- Tagged retrieval for relevant context

### 3. Validation & Error Handling
- Context validated before passing
- Early detection of missing fields
- Clear error messages

### 4. Scalability
- Easy to add new agents (just register blueprint)
- Context window optimization
- Memory management prevents bloat

### 5. Transparency
- All context messages logged
- Blueprints document agent capabilities
- Audit trail for debugging

## Integration Points

### Elite Orchestrator

The `EliteOrchestrator` uses Context Engine in all phases:

- **Data Collection**: Stores data in context memory
- **Analysis**: Validates context flow, sends context messages
- **Risk Assessment**: Retrieves relevant memories
- **Execution**: Uses context for decision-making
- **Audit**: Logs all context interactions

### MCP Trading Orchestrator

The `MCPTradingOrchestrator` validates context flow:

- Validates research → signal → risk → execution flow
- Stores sentiment and analysis in memory
- Sends structured messages between agents

## Future Enhancements

1. **Context Compression**: Compress old memories to save space
2. **Context Versioning**: Track changes to blueprints over time
3. **Context Analytics**: Analyze which contexts are most effective
4. **Multi-Modal Context**: Support for images, charts, etc.
5. **Context Caching**: Cache frequently accessed contexts
6. **Context Sharing**: Share contexts across multiple runs

## References

- [Context Engineering for Multi-Agent Systems](https://www.packtpub.com/en-us/product/context-engineering-for-multi-agent-systems-9781806690046)
- [Context Engineering for Multi-Agent LLM Code Assistants](https://arxiv.org/abs/2508.08322)
- [Model Context Protocol (MCP)](https://modelcontextprotocol.io/)

## Code References

- Context Engine: `src/agent_framework/context_engine.py`
- Agent Blueprints: `src/agent_framework/agent_blueprints.py`
- Elite Orchestrator Integration: `src/orchestration/elite_orchestrator.py`
- MCP Orchestrator Integration: `src/orchestration/mcp_trading.py`
