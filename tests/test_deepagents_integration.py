"""
Tests for deepagents integration.

Note: These tests require Python 3.11-3.13 due to langchain-core compatibility.
Python 3.14 has known compatibility issues.
"""

import pytest
import sys
from unittest.mock import Mock, patch

# Skip tests on Python 3.14+
pytestmark = pytest.mark.skipif(
    sys.version_info >= (3, 14),
    reason="Python 3.14 has compatibility issues with langchain-core",
)


def test_build_trading_tools():
    """Test that trading tools can be built."""
    from src.deepagents_integration.tools import build_trading_tools
    
    tools = build_trading_tools()
    assert len(tools) >= 4, "Should have at least 4 trading tools"
    
    tool_names = [tool.name for tool in tools]
    assert "get_market_data" in tool_names
    assert "query_sentiment" in tool_names
    assert "get_sentiment_history" in tool_names
    assert "analyze_technical_indicators" in tool_names


def test_build_mcp_tools():
    """Test that MCP tools can be built."""
    from src.deepagents_integration.mcp_tools import build_mcp_tools_for_deepagents
    
    tools = build_mcp_tools_for_deepagents()
    assert len(tools) >= 2, "Should have at least 2 MCP tools"
    
    tool_names = [tool.name for tool in tools]
    assert "call_mcp_tool" in tool_names
    assert "get_mcp_servers" in tool_names


def test_trading_tools_import():
    """Test that trading tools can be imported."""
    from src.deepagents_integration.tools import (
        get_market_data,
        query_sentiment,
        get_sentiment_history,
        analyze_technical_indicators,
    )
    
    assert callable(get_market_data)
    assert callable(query_sentiment)
    assert callable(get_sentiment_history)
    assert callable(analyze_technical_indicators)


@patch("src.deepagents_integration.tools.get_market_data_provider")
def test_get_market_data_tool(mock_provider):
    """Test get_market_data tool execution."""
    import pandas as pd
    from datetime import datetime
    from src.deepagents_integration.tools import get_market_data
    
    # Mock market data provider
    mock_df = pd.DataFrame(
        {
            "Open": [100.0, 101.0],
            "High": [102.0, 103.0],
            "Low": [99.0, 100.0],
            "Close": [101.0, 102.0],
            "Volume": [1000000, 1100000],
        },
        index=pd.date_range("2025-01-01", periods=2),
    )
    
    mock_provider_instance = Mock()
    mock_provider_instance.get_daily_bars.return_value = mock_df
    mock_provider.return_value = mock_provider_instance
    
    result = get_market_data("SPY", lookback_days=60)
    
    assert isinstance(result, str)
    import json
    data = json.loads(result)
    assert "symbol" in data
    assert data["symbol"] == "SPY"
    assert "data" in data


def test_mcp_tools_import():
    """Test that MCP tools can be imported."""
    from src.deepagents_integration.mcp_tools import (
        call_mcp_tool,
        get_mcp_servers,
    )
    
    assert callable(call_mcp_tool)
    assert callable(get_mcp_servers)


@patch("src.deepagents_integration.agents.init_chat_model")
@patch("src.deepagents_integration.agents.create_deep_agent")
def test_create_trading_research_agent(mock_create_agent, mock_init_model):
    """Test trading research agent creation."""
    from src.deepagents_integration.agents import create_trading_research_agent
    
    mock_model = Mock()
    mock_init_model.return_value = mock_model
    mock_agent = Mock()
    mock_create_agent.return_value = mock_agent
    
    agent = create_trading_research_agent()
    
    assert agent == mock_agent
    mock_create_agent.assert_called_once()
    call_kwargs = mock_create_agent.call_args[1]
    assert "system_prompt" in call_kwargs
    assert "tools" in call_kwargs


@patch("src.deepagents_integration.agents.init_chat_model")
@patch("src.deepagents_integration.agents.create_deep_agent")
def test_create_market_analysis_agent(mock_create_agent, mock_init_model):
    """Test market analysis agent creation."""
    from src.deepagents_integration.agents import create_market_analysis_agent
    
    mock_model = Mock()
    mock_init_model.return_value = mock_model
    mock_agent = Mock()
    mock_create_agent.return_value = mock_agent
    
    subagents = [{"name": "test-subagent", "description": "Test"}]
    agent = create_market_analysis_agent(subagents=subagents)
    
    assert agent == mock_agent
    mock_create_agent.assert_called_once()
    call_kwargs = mock_create_agent.call_args[1]
    assert "subagents" in call_kwargs
    assert call_kwargs["subagents"] == subagents


def test_deepagents_integration_module():
    """Test that the main module can be imported."""
    from src.deepagents_integration import (
        build_trading_tools,
        create_trading_research_agent,
        create_market_analysis_agent,
        build_mcp_tools_for_deepagents,
    )
    
    assert callable(build_trading_tools)
    assert callable(create_trading_research_agent)
    assert callable(create_market_analysis_agent)
    assert callable(build_mcp_tools_for_deepagents)

