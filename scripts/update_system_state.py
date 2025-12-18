#!/usr/bin/env python3
"""
Update system_state.json from live Alpaca data.

This script ensures local state files stay in sync with actual broker data.
Should be run after every trading session or on-demand when data is stale.

Usage:
    python3 scripts/update_system_state.py
"""

import json
import os
import sys
from datetime import datetime
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))


def update_system_state():
    """Fetch latest data from Alpaca and update system_state.json."""
    try:
        from alpaca.trading.client import TradingClient
    except ImportError:
        print("ERROR: alpaca-py not installed. Run: pip install alpaca-py")
        return False

    api_key = os.environ.get("ALPACA_API_KEY")
    secret_key = os.environ.get("ALPACA_SECRET_KEY")

    if not api_key or not secret_key:
        print("ERROR: ALPACA_API_KEY and ALPACA_SECRET_KEY must be set")
        return False

    # Connect to Alpaca
    client = TradingClient(api_key, secret_key, paper=True)
    account = client.get_account()
    positions = client.get_all_positions()

    # Load existing state
    state_path = Path(__file__).parent.parent / "data" / "system_state.json"
    if state_path.exists():
        with open(state_path) as f:
            state = json.load(f)
    else:
        state = {"meta": {}, "account": {}, "performance": {}}

    # Update account data
    equity = float(account.equity)
    cash = float(account.cash)
    last_equity = float(account.last_equity)

    state["meta"]["last_updated"] = datetime.utcnow().isoformat()
    state["account"]["current_equity"] = equity
    state["account"]["cash"] = cash
    state["account"]["buying_power"] = float(account.buying_power)

    # Calculate P/L from starting balance
    starting_balance = state["account"].get("starting_balance", 100000.0)
    total_pl = equity - starting_balance
    total_pl_pct = (total_pl / starting_balance) * 100

    state["account"]["total_pl"] = total_pl
    state["account"]["total_pl_pct"] = total_pl_pct

    # Calculate positions value
    positions_value = sum(float(p.market_value) for p in positions)
    state["account"]["positions_value"] = positions_value

    # Save updated state
    with open(state_path, "w") as f:
        json.dump(state, f, indent=2)

    # Also update performance log
    perf_path = Path(__file__).parent.parent / "data" / "performance_log.json"
    today = datetime.utcnow().strftime("%Y-%m-%d")

    if perf_path.exists():
        with open(perf_path) as f:
            perf_log = json.load(f)
    else:
        perf_log = []

    # Add or update today's entry
    today_entry = {
        "date": today,
        "equity": equity,
        "cash": cash,
        "pl": total_pl,
        "pl_pct": total_pl_pct,
        "positions_count": len(positions),
        "day_pl": equity - last_equity,
    }

    # Remove existing today entry if present
    perf_log = [e for e in perf_log if e.get("date") != today]
    perf_log.append(today_entry)

    with open(perf_path, "w") as f:
        json.dump(perf_log, f, indent=2)

    print(f"Updated system_state.json:")
    print(f"  Equity: ${equity:,.2f}")
    print(f"  Cash: ${cash:,.2f}")
    print(f"  Total P/L: ${total_pl:+,.2f} ({total_pl_pct:+.2f}%)")
    print(f"  Day P/L: ${equity - last_equity:+,.2f}")
    print(f"  Positions: {len(positions)}")

    return True


if __name__ == "__main__":
    success = update_system_state()
    sys.exit(0 if success else 1)
