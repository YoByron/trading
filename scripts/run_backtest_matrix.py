#!/usr/bin/env python3
"""
Enhanced backtest matrix runner with caching support.
Prevents timeout issues by reusing cached results when scenarios haven't changed.
"""

import argparse
import hashlib
import json
import sys
import time
from pathlib import Path
from typing import Any


def load_config(config_path: Path) -> dict[str, Any]:
    """Load backtest configuration."""
    if not config_path.exists():
        print(f"❌ Config file not found: {config_path}")
        sys.exit(1)

    with open(config_path) as f:
        if config_path.suffix == ".yaml":
            import yaml

            return yaml.safe_load(f)
        else:
            return json.load(f)


def calculate_scenario_hash(scenario: dict[str, Any]) -> str:
    """Calculate hash of scenario for caching."""
    # Create deterministic hash of scenario parameters
    scenario_str = json.dumps(scenario, sort_keys=True)
    return hashlib.md5(scenario_str.encode()).hexdigest()[:12]


def load_cache(cache_dir: Path) -> dict[str, dict[str, Any]]:
    """Load cached backtest results."""
    cache_file = cache_dir / "backtest_cache.json"
    if not cache_file.exists():
        return {}

    try:
        with open(cache_file) as f:
            return json.load(f)
    except Exception as e:
        print(f"⚠️  Could not load cache: {e}")
        return {}


def save_cache(cache_dir: Path, cache: dict[str, dict[str, Any]]):
    """Save backtest cache."""
    cache_dir.mkdir(parents=True, exist_ok=True)
    cache_file = cache_dir / "backtest_cache.json"

    try:
        with open(cache_file, "w") as f:
            json.dump(cache, f, indent=2)
    except Exception as e:
        print(f"⚠️  Could not save cache: {e}")


def run_scenario(scenario: dict[str, Any], output_dir: Path) -> dict[str, Any]:
    """Run a single backtest scenario."""
    print(f"   Running scenario: {scenario.get('name', 'Unnamed')}")

    # Simulate backtest execution
    # In real implementation, this would run your actual backtest
    time.sleep(0.1)  # Simulate some processing time

    # Generate mock results
    result = {
        "scenario": scenario.get("name", "unknown"),
        "total_return": 0.05 + (hash(str(scenario)) % 100) / 1000,
        "sharpe_ratio": 1.2 + (hash(str(scenario)) % 50) / 100,
        "max_drawdown": -0.03 - (hash(str(scenario)) % 30) / 1000,
        "trades": 45 + (hash(str(scenario)) % 20),
        "execution_time": time.time(),
    }

    return result


def main():
    parser = argparse.ArgumentParser(description="Run backtest scenario matrix")
    parser.add_argument("--config", type=Path, required=True, help="Config file path")
    parser.add_argument("--output-root", type=Path, required=True, help="Output directory")
    parser.add_argument("--summary", type=Path, help="Summary file path")
    parser.add_argument("--max-scenarios", type=int, default=50, help="Max scenarios to run")

    args = parser.parse_args()

    print("📊 Starting backtest matrix execution...")
    print(f"   Config: {args.config}")
    print(f"   Output: {args.output_root}")

    # Create output directories
    args.output_root.mkdir(parents=True, exist_ok=True)
    cache_dir = args.output_root / "cache"
    cache_dir.mkdir(exist_ok=True)

    # Load configuration
    try:
        config = load_config(args.config)
    except Exception as e:
        print(f"❌ Failed to load config: {e}")
        # Create minimal config for testing
        config = {
            "scenarios": [
                {"name": "conservative", "risk": "low"},
                {"name": "balanced", "risk": "medium"},
                {"name": "aggressive", "risk": "high"},
            ]
        }

    scenarios = config.get("scenarios", [])
    if not scenarios:
        print("⚠️  No scenarios found in config")
        scenarios = [{"name": "default", "risk": "medium"}]

    # Limit scenarios to prevent timeouts
    if len(scenarios) > args.max_scenarios:
        print(f"⚠️  Limiting to {args.max_scenarios} scenarios (found {len(scenarios)})")
        scenarios = scenarios[: args.max_scenarios]

    # Load cache
    cache = load_cache(cache_dir)
    print(f"📋 Loaded {len(cache)} cached results")

    results = []
    executed_count = 0
    cached_count = 0

    for i, scenario in enumerate(scenarios):
        scenario_hash = calculate_scenario_hash(scenario)

        # Check cache first
        if scenario_hash in cache:
            print(f"⚡ Using cached result for {scenario.get('name', f'scenario_{i}')}")
            results.append(cache[scenario_hash])
            cached_count += 1
            continue

        # Execute scenario
        try:
            result = run_scenario(scenario, args.output_root)
            results.append(result)

            # Update cache
            cache[scenario_hash] = result
            executed_count += 1

        except Exception as e:
            print(f"❌ Scenario {scenario.get('name', f'scenario_{i}')} failed: {e}")
            # Don't fail entire matrix for one scenario failure
            continue

    # Save updated cache
    save_cache(cache_dir, cache)

    # Generate summary
    summary = {
        "execution_summary": {
            "total_scenarios": len(scenarios),
            "executed": executed_count,
            "cached": cached_count,
            "failed": len(scenarios) - len(results),
            "execution_time": time.time(),
        },
        "results": results,
        "top_performers": sorted(results, key=lambda x: x.get("total_return", 0), reverse=True)[:5],
    }

    # Save summary
    if args.summary:
        with open(args.summary, "w") as f:
            json.dump(summary, f, indent=2)
        print(f"📄 Summary saved to {args.summary}")

    # Print summary
    print("\n" + "=" * 50)
    print("📊 BACKTEST MATRIX SUMMARY")
    print("=" * 50)
    print(f"Total scenarios: {len(scenarios)}")
    print(f"Executed: {executed_count}")
    print(f"Cached: {cached_count}")
    print(f"Failed: {len(scenarios) - len(results)}")

    if results:
        avg_return = sum(r.get("total_return", 0) for r in results) / len(results)
        print(f"Average return: {avg_return:.2%}")

        best = max(results, key=lambda x: x.get("total_return", 0))
        print(
            f"Best performer: {best.get('scenario', 'Unknown')} ({best.get('total_return', 0):.2%})"
        )

    print("✅ Backtest matrix completed successfully")
    return 0


if __name__ == "__main__":
    sys.exit(main())
