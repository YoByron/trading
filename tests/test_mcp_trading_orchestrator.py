from __future__ import annotations

from mcp.servers import alpaca as alpaca_tools
from mcp.servers import openrouter as openrouter_tools
from src.orchestration.mcp_trading import MCPTradingOrchestrator


def _mock_bars():
    return [
        {
            "timestamp": "2025-11-03T00:00:00Z",
            "open": 100.0,
            "high": 102.0,
            "low": 99.0,
            "close": 101.0,
            "volume": 1_000_000,
        },
        {
            "timestamp": "2025-11-04T00:00:00Z",
            "open": 101.0,
            "high": 103.0,
            "low": 100.5,
            "close": 102.5,
            "volume": 1_100_000,
        },
    ]


def test_run_once_generates_summary(monkeypatch):
    monkeypatch.setattr(
        alpaca_tools,
        "get_account_snapshot",
        lambda paper: {"portfolio_value": 10000.0},
    )
    monkeypatch.setattr(
        alpaca_tools,
        "get_latest_bars",
        lambda symbols, limit, paper: {symbols[0]: _mock_bars()},
    )
    monkeypatch.setattr(
        openrouter_tools,
        "detailed_sentiment",
        lambda market_data, news: {"score": 0.25, "confidence": 0.8},
    )

    orchestrator = MCPTradingOrchestrator(symbols=["SPY"])

    monkeypatch.setattr(
        orchestrator.meta_agent,
        "analyze",
        lambda data: {"coordinated_decision": {"action": "BUY", "confidence": 0.7}},
    )
    monkeypatch.setattr(
        orchestrator.risk_agent,
        "analyze",
        lambda data: {"action": "APPROVE", "position_size": 100.0},
    )
    monkeypatch.setattr(
        orchestrator.execution_agent,
        "analyze",
        lambda data: {"action": "EXECUTE", "status": "SIMULATED"},
    )

    summary = orchestrator.run_once(execute_orders=True)

    assert summary["mode"] == "paper"
    assert summary["symbols"], "Expected at least one symbol in summary"
    first_symbol = summary["symbols"][0]
    assert first_symbol["symbol"] == "SPY"
    assert first_symbol["meta_decision"]["coordinated_decision"]["action"] == "BUY"
    assert first_symbol["risk_assessment"]["position_size"] == 100.0
    assert first_symbol["execution_plan"]["action"] == "EXECUTE"
