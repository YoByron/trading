"""
Stub definitions for deleted agent_framework module.

The agent_framework was deleted as dormant code, but many files still reference it.
These stubs prevent import errors without restoring 9,914 lines of unused code.
"""
from typing import Any


class RunContext:
    """Stub for deleted RunContext"""

    def __init__(self, **kwargs):
        self.config = kwargs.get("config", {})
        self.state_cache = kwargs.get("state", {})


class RunMode:
    """Stub for deleted RunMode"""

    PAPER = "paper"
    LIVE = "live"


class AgentResult:
    """Stub for deleted AgentResult"""

    def __init__(self, name: str, succeeded: bool, payload: Any = None, error: str | None = None):
        self.name = name
        self.succeeded = succeeded
        self.payload = payload or {}
        self.error = error

    def get(self, key: str, default: Any = None) -> Any:
        return getattr(self, key, default)


class TradingAgent:
    """Stub for deleted TradingAgent"""

    def __init__(self, agent_name: str = "unnamed"):
        self.agent_name = agent_name

    def execute(self, context: RunContext) -> AgentResult:
        return AgentResult(self.agent_name, False, error="agent_framework deleted")


class ContextEngine:
    """Stub for deleted ContextEngine"""

    def send_context_message(self, **kwargs):
        pass  # no-op


class ContextType:
    """Stub for deleted ContextType"""

    TASK_CONTEXT = "TASK_CONTEXT"


class MemoryTimescale:
    """Stub for deleted MemoryTimescale"""

    INTRADAY = "intraday"


class CoEvolutionEngine:
    """Stub for deleted CoEvolutionEngine"""

    def __init__(self, **kwargs):
        pass

    def evolve(self, context: RunContext) -> dict:
        return {"status": "disabled", "reason": "agent_framework deleted"}


def get_context_engine(**kwargs) -> ContextEngine:
    """Stub for deleted get_context_engine"""
    return ContextEngine()


class agent_blueprints:
    """Stub for deleted agent_blueprints"""

    @staticmethod
    def register_trading_agent_blueprints():
        pass  # no-op
