"""
Agent framework scaffolding for the multi-agent trading system.

Exports base interfaces, run context dataclasses, state provider helpers,
and context engineering components.
"""

from .base import TradingAgent, AgentResult
from .context import RunContext, RunMode, AgentConfig
from .state import StateProvider, FileStateProvider
from .context_engine import (
    ContextEngine,
    SemanticBlueprint,
    ContextMessage,
    ContextMemory,
    ContextType,
    ContextPriority,
    get_context_engine
)
from . import agent_blueprints

# Agent0 Co-Evolution components
try:
    from .curriculum_agent import CurriculumAgent, TradingTask, TaskDifficulty, TaskCategory
    from .executor_agent import ExecutorAgent, TaskSolution
    from .coevolution_engine import CoEvolutionEngine, EvolutionStage, EvolutionMetrics
except ImportError:
    # Graceful degradation if dependencies missing
    CurriculumAgent = None
    TradingTask = None
    TaskDifficulty = None
    TaskCategory = None
    ExecutorAgent = None
    TaskSolution = None
    CoEvolutionEngine = None
    EvolutionStage = None
    EvolutionMetrics = None

__all__ = [
    "TradingAgent",
    "AgentResult",
    "RunContext",
    "RunMode",
    "AgentConfig",
    "StateProvider",
    "FileStateProvider",
    "ContextEngine",
    "SemanticBlueprint",
    "ContextMessage",
    "ContextMemory",
    "ContextType",
    "ContextPriority",
    "get_context_engine",
    "agent_blueprints",
    # Agent0 exports
    "CurriculumAgent",
    "TradingTask",
    "TaskDifficulty",
    "TaskCategory",
    "ExecutorAgent",
    "TaskSolution",
    "CoEvolutionEngine",
    "EvolutionStage",
    "EvolutionMetrics",
]

