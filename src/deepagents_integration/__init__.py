"""
DeepAgents Integration for Trading System

This module provides deepagents-based agents with trading-specific tools,
planning capabilities, and sub-agent delegation for complex trading workflows.
"""

from .tools import build_trading_tools
from .agents import create_trading_research_agent, create_market_analysis_agent
from .mcp_tools import build_mcp_tools_for_deepagents

__all__ = [
    "build_trading_tools",
    "create_trading_research_agent",
    "create_market_analysis_agent",
    "build_mcp_tools_for_deepagents",
]
