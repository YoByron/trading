"""
Agent framework scaffolding for the multi-agent trading system.

Exports base interfaces, run context dataclasses, and state provider helpers.
"""

from .base import TradingAgent, AgentResult
from .context import RunContext, RunMode, AgentConfig
from .state import StateProvider, FileStateProvider

__all__ = [
    "TradingAgent",
    "AgentResult",
    "RunContext",
    "RunMode",
    "AgentConfig",
    "StateProvider",
    "FileStateProvider",
]

