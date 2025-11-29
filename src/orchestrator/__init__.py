"""
Trading orchestrator package.

Provides the CLI entrypoint and helper utilities for coordinating agents.
"""

from .main import TradingOrchestrator, OrchestratorConfig

__all__ = ["TradingOrchestrator", "OrchestratorConfig"]
