"""
Strategy Registry - Canonical Pipeline for All Strategies

This registry ensures all strategies follow a standard pipeline and avoids
duplicate work across branches/PRs.

Standard Pipeline:
    data_ingest/ → features/ → signals/ → backtest/ → report/ → execution/

Author: Trading System
Created: 2025-12-02
"""

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger(__name__)

REGISTRY_FILE = Path(__file__).parent.parent.parent / "data" / "strategy_registry.json"


@dataclass
class StrategyMetadata:
    """Metadata for a registered strategy."""

    name: str
    module_path: str
    class_name: str
    description: str
    pipeline_stage: str  # data_ingest, features, signals, backtest, report, execution
    last_backtest_date: Optional[str] = None
    last_backtest_metrics: Optional[dict[str, Any]] = None
    registered_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    branches_touching: list[str] = field(default_factory=list)
    prs_touching: list[str] = field(default_factory=list)


@dataclass
class StrategyRegistry:
    """Registry of all strategies in the system."""

    strategies: dict[str, StrategyMetadata] = field(default_factory=dict)
    last_updated: str = field(default_factory=lambda: datetime.now().isoformat())

    def register(
        self,
        name: str,
        module_path: str,
        class_name: str,
        description: str,
        pipeline_stage: str = "signals",
    ) -> None:
        """
        Register a new strategy.

        Args:
            name: Strategy name (unique identifier)
            module_path: Python module path (e.g., "src.strategies.core_strategy")
            class_name: Strategy class name (e.g., "CoreStrategy")
            description: Human-readable description
            pipeline_stage: Current pipeline stage
        """
        if name in self.strategies:
            # Update existing
            strategy = self.strategies[name]
            strategy.module_path = module_path
            strategy.class_name = class_name
            strategy.description = description
            strategy.pipeline_stage = pipeline_stage
            strategy.updated_at = datetime.now().isoformat()
        else:
            # Create new
            self.strategies[name] = StrategyMetadata(
                name=name,
                module_path=module_path,
                class_name=class_name,
                description=description,
                pipeline_stage=pipeline_stage,
            )

    def update_backtest(
        self,
        name: str,
        backtest_date: str,
        metrics: dict[str, Any],
    ) -> None:
        """
        Update backtest results for a strategy.

        Args:
            name: Strategy name
            backtest_date: Backtest date (YYYY-MM-DD)
            metrics: Backtest metrics dictionary
        """
        if name not in self.strategies:
            logger.warning(f"Strategy {name} not found in registry. Registering it first.")
            self.register(name, "", "", "", "backtest")

        strategy = self.strategies[name]
        strategy.last_backtest_date = backtest_date
        strategy.last_backtest_metrics = metrics
        strategy.updated_at = datetime.now().isoformat()

    def add_branch_reference(self, name: str, branch_name: str) -> None:
        """Add a branch that touches this strategy."""
        if name not in self.strategies:
            logger.warning(f"Strategy {name} not found in registry.")
            return

        if branch_name not in self.strategies[name].branches_touching:
            self.strategies[name].branches_touching.append(branch_name)
            self.strategies[name].updated_at = datetime.now().isoformat()

    def add_pr_reference(self, name: str, pr_number: str) -> None:
        """Add a PR that touches this strategy."""
        if name not in self.strategies:
            logger.warning(f"Strategy {name} not found in registry.")
            return

        if pr_number not in self.strategies[name].prs_touching:
            self.strategies[name].prs_touching.append(pr_number)
            self.strategies[name].updated_at = datetime.now().isoformat()

    def get_strategy(self, name: str) -> Optional[StrategyMetadata]:
        """Get strategy metadata by name."""
        return self.strategies.get(name)

    def list_strategies(self, pipeline_stage: Optional[str] = None) -> list[StrategyMetadata]:
        """
        List all strategies, optionally filtered by pipeline stage.

        Args:
            pipeline_stage: Optional pipeline stage filter

        Returns:
            List of strategy metadata
        """
        strategies = list(self.strategies.values())
        if pipeline_stage:
            strategies = [s for s in strategies if s.pipeline_stage == pipeline_stage]
        return sorted(strategies, key=lambda x: x.updated_at, reverse=True)

    def to_dict(self) -> dict[str, Any]:
        """Convert registry to dictionary for serialization."""
        return {
            "strategies": {
                name: {
                    "name": s.name,
                    "module_path": s.module_path,
                    "class_name": s.class_name,
                    "description": s.description,
                    "pipeline_stage": s.pipeline_stage,
                    "last_backtest_date": s.last_backtest_date,
                    "last_backtest_metrics": s.last_backtest_metrics,
                    "registered_at": s.registered_at,
                    "updated_at": s.updated_at,
                    "branches_touching": s.branches_touching,
                    "prs_touching": s.prs_touching,
                }
                for name, s in self.strategies.items()
            },
            "last_updated": self.last_updated,
        }

    def save(self, filepath: Optional[Path] = None) -> None:
        """Save registry to JSON file."""
        filepath = filepath or REGISTRY_FILE
        filepath.parent.mkdir(parents=True, exist_ok=True)

        self.last_updated = datetime.now().isoformat()
        with open(filepath, "w") as f:
            json.dump(self.to_dict(), f, indent=2)

    @classmethod
    def load(cls, filepath: Optional[Path] = None) -> "StrategyRegistry":
        """Load registry from JSON file."""
        filepath = filepath or REGISTRY_FILE

        if not filepath.exists():
            logger.info(f"Registry file not found at {filepath}. Creating new registry.")
            return cls()

        with open(filepath, "r") as f:
            data = json.load(f)

        registry = cls()
        registry.last_updated = data.get("last_updated", datetime.now().isoformat())

        for name, strategy_data in data.get("strategies", {}).items():
            registry.strategies[name] = StrategyMetadata(
                name=strategy_data["name"],
                module_path=strategy_data["module_path"],
                class_name=strategy_data["class_name"],
                description=strategy_data["description"],
                pipeline_stage=strategy_data["pipeline_stage"],
                last_backtest_date=strategy_data.get("last_backtest_date"),
                last_backtest_metrics=strategy_data.get("last_backtest_metrics"),
                registered_at=strategy_data.get("registered_at", datetime.now().isoformat()),
                updated_at=strategy_data.get("updated_at", datetime.now().isoformat()),
                branches_touching=strategy_data.get("branches_touching", []),
                prs_touching=strategy_data.get("prs_touching", []),
            )

        return registry


# Global registry instance
_registry: Optional[StrategyRegistry] = None


def get_registry() -> StrategyRegistry:
    """Get or create global registry instance."""
    global _registry
    if _registry is None:
        _registry = StrategyRegistry.load()
    return _registry


def register_strategy(
    name: str,
    module_path: str,
    class_name: str,
    description: str,
    pipeline_stage: str = "signals",
) -> None:
    """
    Convenience function to register a strategy.

    Args:
        name: Strategy name
        module_path: Python module path
        class_name: Strategy class name
        description: Description
        pipeline_stage: Pipeline stage
    """
    registry = get_registry()
    registry.register(name, module_path, class_name, description, pipeline_stage)
    registry.save()


def update_backtest_results(
    name: str,
    backtest_date: str,
    metrics: dict[str, Any],
) -> None:
    """
    Convenience function to update backtest results.

    Args:
        name: Strategy name
        backtest_date: Backtest date
        metrics: Backtest metrics
    """
    registry = get_registry()
    registry.update_backtest(name, backtest_date, metrics)
    registry.save()
