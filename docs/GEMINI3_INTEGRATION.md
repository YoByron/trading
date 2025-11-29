# Gemini 3 AI Agent Integration

**Date**: November 20, 2025
**Status**: ✅ Implemented
**Based on**: [Google Gemini 3 AI Agents Guide](https://developers.googleblog.com/building-ai-agents-with-google-gemini-3-and-open-source-frameworks/)

---

## 🎯 Overview

Enhanced trading system with Google Gemini 3 AI agents using best practices:

- **Thinking Level Control**: Adjust reasoning depth per request
- **Thought Signatures**: Stateful multi-step execution
- **LangGraph Orchestration**: Multi-agent workflow
- **Multimodal Capabilities**: Chart analysis

---

## 🔑 Key Features

### 1. Thinking Level Control

Control reasoning depth dynamically:

```python
from src.agents.gemini3_integration import get_gemini3_integration

integration = get_gemini3_integration()

# High thinking for complex analysis
result = integration.analyze_market(
    symbols=["SPY", "QQQ"],
    market_data=data,
    thinking_level="high",  # Deep reasoning
)

# Low thinking for quick decisions
result = integration.analyze_market(
    symbols=["SPY"],
    market_data=data,
    thinking_level="low",  # Fast response
)
```

**Thinking Levels**:
- `low`: Quick responses, minimal reasoning
- `medium`: Balanced reasoning (default)
- `high`: Deep analysis, comprehensive reasoning

### 2. Thought Signatures

Preserve reasoning context across multi-step execution:

```python
result = integration.analyze_market(...)

# Thought signatures preserved automatically
thought_sigs = result.get("thought_signatures", [])
# Agent maintains exact train of thought
```

### 3. Multi-Agent Orchestration

LangGraph workflow with three agents:

1. **Research Agent** (high thinking): Gathers market data
2. **Analysis Agent** (medium thinking): Technical/fundamental analysis
3. **Decision Agent** (low thinking): Final trading decision

### 4. Multimodal Chart Analysis

Analyze price charts with images:

```python
result = integration.analyze_chart(
    chart_path="charts/spy_chart.png",
    symbol="SPY",
    thinking_level="high",
)
```

---

## 🚀 Usage

### Basic Market Analysis

```python
from src.agents.gemini3_integration import get_gemini3_integration

integration = get_gemini3_integration()

market_data = {
    "symbols": ["SPY", "QQQ", "VOO"],
    "market_regime": "neutral",
    "volatility": "moderate",
}

result = integration.analyze_market(
    symbols=["SPY", "QQQ"],
    market_data=market_data,
    thinking_level="medium",
)

decision = result.get("decision", {})
print(f"Action: {decision.get('action')}")
print(f"Confidence: {decision.get('confidence')}")
```

### Chart Analysis

```python
result = integration.analyze_chart(
    chart_path="data/charts/spy_daily.png",
    symbol="SPY",
    thinking_level="high",
)

print(result["analysis"])
```

### Integration with Trading Strategy

```python
from src.strategies.core_strategy import CoreStrategy
from src.agents.gemini3_integration import get_gemini3_integration

# In CoreStrategy.execute_daily()
gemini3 = get_gemini3_integration()

if gemini3.enabled:
    # Get AI recommendation
    recommendation = gemini3.get_trading_recommendation(
        symbol="SPY",
        market_context=market_data,
        thinking_level="high",
    )

    # Use recommendation in decision
    if recommendation.get("decision", {}).get("action") == "BUY":
        # Execute trade
        pass
```

---

## 📊 Architecture

```
┌─────────────────────────────────────────┐
│  Gemini3TradingIntegration              │
│  (Integration Layer)                     │
└──────────────┬──────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────┐
│  Gemini3LangGraphAgent                  │
│  (Multi-Agent System)                    │
└──────────────┬──────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────┐
│  LangGraph Workflow                      │
│  ┌──────────┐  ┌──────────┐  ┌────────┐│
│  │ Research │→ │ Analysis │→ │Decision││
│  │ (high)   │  │ (medium) │  │ (low)  ││
│  └──────────┘  └──────────┘  └────────┘│
└─────────────────────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────┐
│  Google Gemini 3 API                    │
│  - Thinking level control                │
│  - Thought signatures                   │
│  - Multimodal capabilities               │
└─────────────────────────────────────────┘
```

---

## ⚙️ Configuration

### Environment Variables

```bash
export GOOGLE_API_KEY="your_gemini_api_key"
```

### Model Selection

Default: `gemini-3.0-pro`

Available models:
- `gemini-3.0-pro`: Full capabilities
- `gemini-2.5-flash`: Faster, lighter

---

## 📈 Benefits

1. **Adaptive Reasoning**: Adjust depth based on task complexity
2. **Stateful Execution**: Maintain context across multi-step operations
3. **Multi-Agent Coordination**: Specialized agents for different tasks
4. **Chart Analysis**: Visual analysis capabilities
5. **Better Decisions**: Deeper reasoning improves trading decisions

---

## 🔧 Integration Points

### With CoreStrategy

```python
# In src/strategies/core_strategy.py
from src.agents.gemini3_integration import get_gemini3_integration

class CoreStrategy:
    def execute_daily(self):
        # ... existing logic ...

        # Add Gemini 3 validation
        gemini3 = get_gemini3_integration()
        if gemini3.enabled:
            recommendation = gemini3.get_trading_recommendation(
                symbol=best_etf,
                market_context=context,
                thinking_level="high",
            )

            if recommendation.get("decision", {}).get("action") != "BUY":
                logger.warning("Gemini 3 recommends against trade")
                return None
```

### With Risk Management

```python
# Use Gemini 3 for risk assessment
result = gemini3.analyze_market(
    symbols=["SPY"],
    market_data=risk_data,
    thinking_level="high",  # Deep risk analysis
)
```

---

## 🧪 Testing

```bash
# Test Gemini 3 integration
python3 scripts/gemini3_trading_analysis.py
```

---

## 📚 References

- [Google Gemini 3 Blog Post](https://developers.googleblog.com/building-ai-agents-with-google-gemini-3-and-open-source-frameworks/)
- [LangGraph Documentation](https://langchain-ai.github.io/langgraph/)
- [Gemini API Documentation](https://ai.google.dev/docs)

---

## ✅ Status

- ✅ Thinking level control implemented
- ✅ Thought signatures preserved
- ✅ LangGraph multi-agent workflow
- ✅ Multimodal chart analysis ready
- ✅ Integration layer complete
- ⚠️ Requires GOOGLE_API_KEY to enable

---

## 🎯 Next Steps

1. **Production Integration**: Integrate with CoreStrategy
2. **Chart Generation**: Auto-generate charts for analysis
3. **Performance Monitoring**: Track Gemini 3 decision quality
4. **Cost Optimization**: Monitor API usage and costs
