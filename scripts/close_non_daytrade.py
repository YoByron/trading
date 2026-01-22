#!/usr/bin/env python3
"""Close positions using Alpaca's close_position API."""

import os
import sys
from datetime import datetime

api_key = os.environ.get("ALPACA_API_KEY") or os.environ.get("ALPACA_PAPER_TRADING_5K_API_KEY")
api_secret = os.environ.get("ALPACA_SECRET_KEY") or os.environ.get(
    "ALPACA_PAPER_TRADING_5K_API_SECRET"
)

if not api_key or not api_secret:
    print("ERROR: Missing Alpaca API credentials")
    sys.exit(1)

from alpaca.trading.client import TradingClient

print("=" * 60)
print(f"CLOSE POSITION VIA API - {datetime.now()}")
print("=" * 60)

client = TradingClient(api_key, api_secret, paper=True)
account = client.get_account()
print(f"\nEquity: ${float(account.equity):,.2f}")
print(f"Day Trade Count: {account.daytrade_count}")

target = "SPY260220P00658000"

# Get current position
positions = client.get_all_positions()
target_pos = None
for p in positions:
    if p.symbol == target:
        target_pos = p
        print(f"\nFound: {target}")
        print(f"  Qty: {p.qty}")
        print(f"  Current Price: ${float(p.current_price):.2f}")
        print(f"  P/L: ${float(p.unrealized_pl):+,.2f}")
        break

if not target_pos:
    print(f"\n{target} not found - may already be closed")
    sys.exit(0)

# Use close_position API - this properly closes the position
print("\nClosing position via close_position API...")
try:
    result = client.close_position(target)
    print("✅ Position closed!")
    print(f"   Order ID: {result.id if hasattr(result, 'id') else result}")
except Exception as e:
    error_msg = str(e)
    print(f"❌ Failed: {error_msg}")

    # If PDT error, try closing fewer contracts
    if "day trading" in error_msg.lower():
        print("\nPDT detected - cannot close today")
        sys.exit(1)

    sys.exit(1)

print("\n" + "=" * 60)
print("DONE")
print("=" * 60)
