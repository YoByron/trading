# DeepAgents Integration for Trading System

This module provides a full integration of [deepagents](https://github.com/langchain-ai/deepagents) into the trading system, enabling advanced agent capabilities including:

- **Planning**: Task breakdown and progress tracking with `write_todos`
- **Filesystem Access**: Read/write files for context management and persistence
- **Sub-Agent Delegation**: Isolated sub-agents for specialized tasks
- **Context Management**: Automatic summarization and context offloading
- **Cost Optimization**: Prompt caching for Anthropic models

## Quick Start

```python
from src.deepagents_integration import create_trading_research_agent

# Create a research agent
agent = create_trading_research_agent()

# Use it for research
result = await agent.ainvoke({
    "messages": [{
        "role": "user",
        "content": "Research NVDA stock and provide investment recommendation"
    }]
})
```

## Architecture

### Tools

The integration provides trading-specific tools:

- **Market Data**: `get_market_data`, `analyze_technical_indicators`
- **Sentiment**: `query_sentiment`, `get_sentiment_history`
- **MCP Integration**: `call_mcp_tool`, `get_mcp_servers`

### Agents

#### Trading Research Agent

Comprehensive research agent with planning capabilities:

```python
from src.deepagents_integration import create_trading_research_agent

agent = create_trading_research_agent(
    model="anthropic:claude-sonnet-4-5-20250929",
    include_mcp_tools=True,
    temperature=0.3,
)
```

**Capabilities:**
- Breaks down complex research into manageable steps
- Uses filesystem to save intermediate results
- Delegates specialized analysis to sub-agents
- Generates comprehensive reports

#### Market Analysis Agent

Real-time market analysis with sub-agent delegation:

```python
from src.deepagents_integration import create_market_analysis_agent

# Define sub-agents
risk_subagent = {
    "name": "risk-analyst",
    "description": "Risk assessment specialist",
    "system_prompt": "You assess portfolio risk...",
    "tools": [],
}

agent = create_market_analysis_agent(
    model="anthropic:claude-sonnet-4-5-20250929",
    subagents=[risk_subagent],
    temperature=0.2,
)
```

**Capabilities:**
- Market regime detection
- Trade signal generation
- Risk assessment via sub-agents
- Execution planning

## Built-in DeepAgents Features

### Planning (`write_todos`)

Agents automatically plan complex tasks:

```python
# Agent will use write_todos internally to break down:
# "Research NVDA, analyze sentiment, assess risk, generate report"
# Into:
# 1. Gather market data for NVDA
# 2. Query sentiment data
# 3. Calculate technical indicators
# 4. Assess risk factors
# 5. Generate final report
```

### Filesystem Tools

Agents can read/write files for context management:

- `read_file`: Read analysis files
- `write_file`: Save intermediate results
- `ls`: List available files
- `grep`: Search file contents

### Sub-Agent Delegation (`task`)

Delegate specialized tasks to isolated sub-agents:

```python
# Main agent delegates risk assessment to specialized sub-agent
# This keeps main agent context clean while going deep on specific tasks
```

### Context Management

- Automatic summarization when context exceeds 170K tokens
- Filesystem offloading for large tool results (>20K tokens)
- Keeps last 6 messages intact while summarizing older content

## Examples

See `examples/deepagents_trading_example.py` for complete examples:

1. **Research Agent**: Comprehensive stock research
2. **Market Analysis**: Real-time analysis with sub-agents
3. **Planning Workflow**: Task breakdown demonstration

## Integration with Existing System

The deepagents integration works alongside existing systems:

- **LangChain Agents**: Can use both systems independently
- **MCP Tools**: Full access to all MCP servers
- **Existing Tools**: Wraps existing market data and sentiment utilities
- **Agent Framework**: Compatible with `src/agent_framework`

## Benefits Over Custom Implementation

1. **Standardized Patterns**: Consistent agent architecture
2. **Built-in Middleware**: Planning, filesystem, sub-agents included
3. **Cost Optimization**: Prompt caching reduces API costs
4. **Context Management**: Automatic handling of long conversations
5. **Best Practices**: Implements patterns from Claude Code, Manus

## Configuration

Set environment variables:

```bash
export ANTHROPIC_API_KEY=your_key_here
export LANGCHAIN_MODEL=anthropic:claude-sonnet-4-5-20250929  # Optional
export LANGCHAIN_TEMPERATURE=0.3  # Optional
```

## References

- [DeepAgents Documentation](https://docs.langchain.com/oss/python/deepagents/overview)
- [DeepAgents Quickstarts](https://github.com/langchain-ai/deepagents-quickstarts)
- [LangChain Agents](https://python.langchain.com/docs/modules/agents/)

