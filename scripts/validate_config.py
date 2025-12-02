#!/usr/bin/env python3
"""Validate environment configuration with basic safety checks."""

from __future__ import annotations

from src.core.config import load_config


def main() -> int:
    try:
        cfg = load_config()
        # Print minimal summary
        print("Config OK:")
        print(f"  DAILY_INVESTMENT={cfg.DAILY_INVESTMENT}")
        print(f"  ALPACA_SIMULATED={cfg.ALPACA_SIMULATED}")
        print(f"  HYBRID_LLM_MODEL={cfg.HYBRID_LLM_MODEL}")
        return 0
    except Exception as exc:
        print(f"Config invalid: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
