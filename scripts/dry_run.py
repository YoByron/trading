#!/usr/bin/env python3
"""
Dry Run CLI: Execute planning, data collection, and analysis without placing trades.

Usage:
  python3 scripts/dry_run.py --symbols SPY QQQ VOO

Notes:
  - Loads .env if present.
  - Skips execution phase entirely (no ADK/MCP orders).
  - Prints ensemble vote and top agent recommendations per symbol.
"""
import argparse
import json
import os
from typing import List

try:
    from dotenv import load_dotenv

    load_dotenv()
except Exception:
    pass

import sys
from pathlib import Path

# Ensure project root on sys.path
PROJECT_ROOT = Path(__file__).parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.orchestration.elite_orchestrator import EliteOrchestrator


def dry_run(symbols: List[str]) -> int:
    eo = EliteOrchestrator(paper=True, enable_planning=True)
    plan = eo.create_trade_plan(symbols)

    # Phase 2: Data collection
    data = eo._execute_data_collection(plan)

    # Phase 3: Analysis (ensemble voting)
    analysis = eo._execute_analysis(plan, data)

    print("\n=== Ensemble Vote ===")
    for sym, vote in analysis.get("ensemble_vote", {}).items():
        print(
            f"{sym}: consensus={vote.get('consensus')} buy_votes={vote.get('buy_votes')}/{vote.get('total_votes')}"
        )

    print("\n=== Agent Recommendations (top 5) ===")
    agent_results = analysis.get("agent_results", [])
    for rec in agent_results[:5]:
        print(json.dumps(rec, indent=2))

    # Phase 4: Risk assessment (informational only)
    risk = eo._execute_risk_assessment(plan)
    print("\n=== Risk Assessment ===")
    print(json.dumps(risk, indent=2, default=str))

    print("\nDry run complete (no trades executed).")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Dry run trading analysis without execution"
    )
    parser.add_argument(
        "--symbols", nargs="*", default=["SPY", "QQQ"], help="Symbols to analyze"
    )
    args = parser.parse_args()
    return dry_run(args.symbols)


if __name__ == "__main__":
    raise SystemExit(main())
