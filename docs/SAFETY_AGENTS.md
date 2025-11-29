# Graham-Buffett Safety Agents

## Overview

Autonomous AI agents that implement Graham-Buffett investment safety principles. These agents work together to ensure we only invest in quality companies at attractive prices.

## Agent Architecture

```
SafetyOrchestratorAgent (Coordinator)
├── SafetyAnalysisAgent (Trade Analysis)
├── QualityMonitorAgent (Portfolio Monitoring)
└── ValueDiscoveryAgent (Opportunity Discovery)
```

## Agents

### 1. Safety Analysis Agent

**Purpose**: Analyze individual investment opportunities using Graham-Buffett principles.

**Responsibilities**:
- Calculate margin of safety (intrinsic value vs market price)
- Screen for quality companies (fundamentals, debt, earnings)
- Enforce circle of competence
- Provide safety ratings and recommendations

**Usage**:
```python
from src.agents.safety_analysis_agent import SafetyAnalysisAgent

agent = SafetyAnalysisAgent()

analysis = agent.analyze({
    "symbol": "AAPL",
    "market_price": 150.00,
    "force_refresh": False
})

# Returns:
# {
#     "action": "APPROVE" | "REJECT",
#     "safety_rating": "excellent" | "good" | "acceptable" | "poor" | "reject",
#     "margin_of_safety_pct": 0.35,  # 35% discount
#     "quality_score": 82.5,
#     "confidence": 0.85,
#     "thesis": "...",
#     ...
# }
```

### 2. Quality Monitor Agent

**Purpose**: Monitor portfolio quality over time and detect deterioration.

**Responsibilities**:
- Track quality scores of all holdings
- Detect quality deterioration
- Recommend position adjustments
- Track quality trends

**Usage**:
```python
from src.agents.quality_monitor_agent import QualityMonitorAgent

agent = QualityMonitorAgent()

report = agent.analyze({
    "positions": [
        {"symbol": "AAPL", "quantity": 10.0, "current_price": 150.00},
        {"symbol": "MSFT", "quantity": 5.0, "current_price": 300.00},
    ],
    "portfolio_value": 3000.00
})

# Returns:
# {
#     "action": "MONITOR" | "ALERT",
#     "portfolio_quality": 75.5,  # Average quality score
#     "alerts": [...],  # Quality deterioration alerts
#     "recommendations": [...],  # Position adjustment recommendations
#     ...
# }
```

### 3. Value Discovery Agent

**Purpose**: Find undervalued investment opportunities.

**Responsibilities**:
- Scan watchlist for undervalued stocks
- Calculate margin of safety for each
- Rank opportunities by safety and value
- Recommend best opportunities

**Usage**:
```python
from src.agents.value_discovery_agent import ValueDiscoveryAgent

agent = ValueDiscoveryAgent()

opportunities = agent.analyze({
    "watchlist": ["AAPL", "MSFT", "GOOGL", "AMZN"],
    "market_prices": {
        "AAPL": 150.00,
        "MSFT": 300.00,
        # ... optional, will fetch if not provided
    }
})

# Returns:
# {
#     "action": "OPPORTUNITIES_FOUND",
#     "total_opportunities": 3,
#     "opportunities": [
#         {
#             "symbol": "AAPL",
#             "margin_of_safety_pct": 0.35,
#             "quality_score": 82.5,
#             "opportunity_score": 87.5,
#             ...
#         },
#         ...
#     ],
#     "top_3_picks": ["AAPL", "MSFT", "GOOGL"],
#     ...
# }
```

### 4. Safety Orchestrator Agent

**Purpose**: Coordinate all safety agents for comprehensive analysis.

**Responsibilities**:
- Orchestrate safety analysis for trades
- Coordinate quality monitoring
- Manage value discovery
- Aggregate recommendations

**Usage**:
```python
from src.agents.safety_orchestrator_agent import SafetyOrchestratorAgent

orchestrator = SafetyOrchestratorAgent()

# Trade Analysis
result = orchestrator.analyze({
    "analysis_type": "trade_analysis",
    "symbol": "AAPL",
    "market_price": 150.00
})

# Quality Monitoring
result = orchestrator.analyze({
    "analysis_type": "quality_monitoring",
    "positions": [...],
    "portfolio_value": 10000.00
})

# Value Discovery
result = orchestrator.analyze({
    "analysis_type": "value_discovery",
    "watchlist": ["AAPL", "MSFT", "GOOGL"],
    "market_prices": {...}
})

# Comprehensive Analysis
result = orchestrator.analyze({
    "analysis_type": "comprehensive",
    "symbol": "AAPL",
    "market_price": 150.00,
    "positions": [...],
    "watchlist": [...]
})
```

## Integration with Trading System

### Automatic Integration

The safety agents are automatically integrated into the core trading strategy. When `USE_GRAHAM_BUFFETT_SAFETY=true` (default), the Safety Analysis Agent runs before every trade execution.

### Manual Integration

You can also use the agents directly in your trading logic:

```python
from src.agents.safety_orchestrator_agent import SafetyOrchestratorAgent

orchestrator = SafetyOrchestratorAgent()

# Before executing a trade
analysis = orchestrator.analyze({
    "analysis_type": "trade_analysis",
    "symbol": "AAPL",
    "market_price": 150.00
})

if analysis["overall_recommendation"] == "APPROVE":
    # Execute trade
    execute_trade(...)
else:
    # Reject trade
    logger.warning(f"Trade rejected: {analysis['safety_analysis']['reasons']}")
```

## Agent Decision Making

All agents use:
1. **Graham-Buffett Safety Module**: Quantitative analysis (margin of safety, quality scores)
2. **LLM Reasoning**: Claude AI for qualitative analysis and insights
3. **Memory**: Learn from past decisions and outcomes
4. **Transparency**: Full audit trail of all decisions

## Configuration

### Environment Variables

```bash
# Enable/disable Graham-Buffett safety (default: true)
USE_GRAHAM_BUFFETT_SAFETY=true

# Minimum margin of safety required (default: 0.20 = 20%)
GRAHAM_BUFFETT_MIN_MARGIN=0.20

# Anthropic API key for LLM reasoning
ANTHROPIC_API_KEY=sk-ant-...
```

### Agent Initialization

```python
# Custom configuration
from src.agents.safety_analysis_agent import SafetyAnalysisAgent

agent = SafetyAnalysisAgent(min_margin_of_safety=0.25)  # Require 25% discount
```

## Example Workflows

### Daily Trading Workflow

```python
from src.agents.safety_orchestrator_agent import SafetyOrchestratorAgent

orchestrator = SafetyOrchestratorAgent()

# 1. Analyze trade opportunity
trade_analysis = orchestrator.analyze({
    "analysis_type": "trade_analysis",
    "symbol": "SPY",
    "market_price": 450.00
})

if trade_analysis["overall_recommendation"] == "APPROVE":
    # 2. Execute trade
    execute_trade("SPY", 450.00)

    # 3. Monitor quality after trade
    quality_report = orchestrator.analyze({
        "analysis_type": "quality_monitoring",
        "positions": get_current_positions(),
        "portfolio_value": get_portfolio_value()
    })
```

### Weekly Portfolio Review

```python
# 1. Monitor portfolio quality
quality_report = orchestrator.analyze({
    "analysis_type": "quality_monitoring",
    "positions": get_all_positions(),
    "portfolio_value": get_portfolio_value()
})

# 2. Check for alerts
if quality_report["quality_report"]["alerts"]:
    for alert in quality_report["quality_report"]["alerts"]:
        logger.warning(f"Quality alert: {alert['message']}")
        # Take action if needed

# 3. Discover new opportunities
opportunities = orchestrator.analyze({
    "analysis_type": "value_discovery",
    "watchlist": get_watchlist(),
})
```

### Comprehensive Analysis

```python
# Run all analyses at once
comprehensive = orchestrator.analyze({
    "analysis_type": "comprehensive",
    "symbol": "AAPL",
    "market_price": 150.00,
    "positions": get_current_positions(),
    "watchlist": get_watchlist(),
})

# Get unified recommendation
synthesis = comprehensive["synthesis"]
if synthesis["investment_readiness"] == "READY":
    # Proceed with investment
    pass
```

## Agent Learning

All agents learn from outcomes:

```python
# After a trade completes, provide feedback
agent.learn_from_outcome(
    decision_id="trade_123",
    outcome={
        "result": "PROFIT",
        "pl": 150.00,
        "quality_maintained": True,
    }
)
```

## Monitoring and Logging

All agent decisions are logged for audit:

```python
# Get decision log
decisions = agent.decision_log

# Get memory context
context = agent.get_memory_context(limit=10)
```

## Best Practices

1. **Always use Safety Orchestrator**: Use the orchestrator for coordinated analysis
2. **Review Rejections**: Check why trades were rejected to understand market conditions
3. **Monitor Quality**: Run quality monitoring regularly (daily/weekly)
4. **Value Discovery**: Use value discovery to find new opportunities
5. **Learn from Outcomes**: Provide feedback to agents for continuous improvement

## Troubleshooting

### Agent Not Responding

- Check `ANTHROPIC_API_KEY` is set
- Verify network connectivity
- Check agent logs for errors

### Safety Analysis Failing

- Ensure DCF calculation is working (check API keys)
- Verify company data is available (Yahoo Finance)
- Check safety module configuration

### Quality Monitoring Not Detecting Issues

- Ensure positions are provided correctly
- Check quality history is being stored
- Verify quality thresholds are appropriate

## Future Enhancements

- [ ] Parallel agent execution for faster analysis
- [ ] Real-time quality monitoring alerts
- [ ] Automated position adjustments based on quality
- [ ] Integration with portfolio rebalancing
- [ ] Multi-timeframe quality analysis

---

**Remember**: These agents are designed to **protect capital** by ensuring we only invest in quality companies at attractive prices. They may reduce trading frequency, but that's by design - quality over quantity.
