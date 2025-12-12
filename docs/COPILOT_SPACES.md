# GitHub Copilot Spaces Configuration

This document defines the curated "Spaces" for this repository to act as specialized "brains" for different domains of the system.
See [GitHub Copilot Spaces Documentation](https://docs.github.com/en/copilot/concepts/context/spaces) for setup instructions.

## 1. Core Trading Engine Space
**Focus**: Operational logic, order execution, risk management, and signal generation.
**Use Case**: "Fix a bug in the risk manager", "Add a new technical indicator", "Refactor the execution flow".

**Key Files & Folders**:
- `src/orchestrator/` (Main funnel logic)
- `src/risk/` (Risk gates and sizing)
- `src/execution/` (Alpaca interaction)
- `src/signals/` (Signal generation)
- `scripts/autonomous_trader.py` (Entrypoint)
- `docs/ops/RUNBOOK.md` (Operational procedures)

## 2. Strategy & ML Research Space
**Focus**: Developing alpha sources, backtesting, and training ML models.
**Use Case**: "Train the RL model", "Add a new backtest scenario", "Analyze model performance".

**Key Files & Folders**:
- `src/ml/` (Machine learning models and pipelines)
- `src/strategies/` (Strategy implementations)
- `src/backtesting/` (Backtesting engine)
- `config/backtest_scenarios.yaml` (Regime definitions)
- `scripts/run_backtest_matrix.py` (Backtest runner)
- `scripts/train_rl_transformer.py` (Training script)

## 3. Infrastructure & Safety Space
**Focus**: CI/CD pipelines, verification protocols, and deployment safety.
**Use Case**: "Update the promotion gate", "Fix a CI failure", "Add a new safety check".

**Key Files & Folders**:
- `.github/workflows/` (CI/CD definitions)
- `src/verification/` (Safety checkers and validators)
- `tests/` (Unit and integration tests)
- `docs/verification-protocols.md` (MANDATORY reading)
- `docs/AGENTS.md` (Agent guidelines)

## 4. Agent Framework Space
**Focus**: The autonomous agent architecture, RAG, and LLM interactions.
**Use Case**: "Create a new agent", "Debug LangChain tools", "Update RAG storage".

**Key Files & Folders**:
- `src/agents/` (Agent implementations)
- `src/agent_framework/` (Base classes)
- `src/rag/` (Retrieval Augmented Generation)
- `src/langchain_agents/` (LangChain integrations)

## Workflow Guidelines

1.  **Select the Space**: Always talk to Copilot *through* the space most relevant to your current task.
2.  **Focus Context**: If answers are generic, ensure you are in the correct space.
3.  **Update Spaces**: As the codebase evolves, add new critical files to these definitions.
