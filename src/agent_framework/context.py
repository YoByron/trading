"""Dataclasses for run configuration and agent context."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, Optional


class RunMode(Enum):
    """Execution mode for an orchestrated run."""

    LIVE = "live"
    PAPER = "paper"
    DRY_RUN = "dry_run"


@dataclass
class AgentConfig:
    """Configuration values injected into agents."""

    data: Dict[str, Any] = field(default_factory=dict)

    def get(self, key: str, default: Optional[Any] = None) -> Any:
        return self.data.get(key, default)


@dataclass
class RunContext:
    """Shared context passed between orchestrator and agents."""

    mode: RunMode
    force: bool = False
    run_id: Optional[str] = None
    config: AgentConfig = field(default_factory=AgentConfig)
    workspace_dir: Path = field(default_factory=lambda: Path.cwd())
    state_cache: Dict[str, Any] = field(default_factory=dict)

    def copy_with(self, **overrides: Any) -> "RunContext":
        """Return a shallow copy with updates."""
        data = self.__dict__.copy()
        data.update(overrides)
        return RunContext(**data)

