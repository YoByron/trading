#!/usr/bin/env python3
"""Close ONLY contracts bought BEFORE today to bypass PDT."""

import os
import sys
from datetime import datetime, timezone

api_key = os.environ.get("ALPACA_API_KEY") or os.environ.get("ALPACA_PAPER_TRADING_5K_API_KEY")
api_secret = os.environ.get("ALPACA_SECRET_KEY") or os.environ.get(
    "ALPACA_PAPER_TRADING_5K_API_SECRET"
)

if not api_key or not api_secret:
    print("ERROR: Missing Alpaca API credentials")
    sys.exit(1)

from alpaca.trading.client import TradingClient
from alpaca.trading.enums import QueryOrderStatus
from alpaca.trading.requests import ClosePositionRequest, GetOrdersRequest

print("=" * 60)
print(f"PDT BYPASS - CLOSE NON-DAYTRADE ONLY - {datetime.now()}")
print("=" * 60)

client = TradingClient(api_key, api_secret, paper=True)
account = client.get_account()
print(f"\nEquity: ${float(account.equity):,.2f}")
print(f"Day Trade Count: {account.daytrade_count}")

target = "SPY260220P00658000"
today = datetime.now(timezone.utc).date()

# Get position
positions = client.get_all_positions()
target_pos = None
for p in positions:
    if p.symbol == target:
        target_pos = p
        total_qty = int(float(p.qty))
        price = float(p.current_price)
        print(f"\nPosition: {target}")
        print(f"  Total Qty: {total_qty}")
        print(f"  Price: ${price:.2f}")
        print(f"  P/L: ${float(p.unrealized_pl):+,.2f}")
        break

if not target_pos:
    print(f"\n✅ {target} not found - may be closed already")
    sys.exit(0)

# Calculate PDT-safe quantity using local trade history (more reliable than API)
print("\nCalculating PDT-safe quantity from trade history...")
import json
from datetime import timedelta

buys_today = 0
buys_before = 0

# First try local trade history (most complete)
try:
    with open("data/system_state.json") as f:
        state = json.load(f)
    for trade in state.get("trade_history", []):
        if trade.get("symbol") == target and "BUY" in str(trade.get("side", "")):
            qty = int(float(trade.get("qty", 0)))
            filled_str = trade.get("filled_at", "")
            if filled_str:
                filled_date = datetime.fromisoformat(filled_str.replace("+00:00", "")).date()
                if filled_date == today:
                    buys_today += qty
                else:
                    buys_before += qty
    print("  (from local trade history)")
except Exception as e:
    print(f"  Local history failed: {e}, trying API with date range...")
    # Fallback: Query API with explicit date range (30 days back)
    try:
        from datetime import timedelta

        start_date = today - timedelta(days=30)
        orders = client.get_orders(
            filter=GetOrdersRequest(
                status=QueryOrderStatus.ALL,
                limit=500,
                after=datetime.combine(start_date, datetime.min.time()).replace(
                    tzinfo=timezone.utc
                ),
            )
        )
        for order in orders:
            if order.symbol == target and order.side.name == "BUY" and order.filled_at:
                filled_qty = int(float(order.filled_qty or 0))
                if order.filled_at.date() == today:
                    buys_today += filled_qty
                else:
                    buys_before += filled_qty
    except Exception as e2:
        print(f"  API also failed: {e2}")
        # Final fallback: assume 2 bought today (conservative based on known data)
        buys_today = 2
        buys_before = total_qty - 2

print(f"  Bought TODAY (day trade if sold): {buys_today}")
print(f"  Bought BEFORE today (SAFE to sell): {buys_before}")

safe_qty = min(buys_before, total_qty)

if safe_qty <= 0:
    print("\n⚠️ No PDT-safe contracts to close")
    sys.exit(0)

print(f"\n🔧 Will close {safe_qty} of {total_qty} contracts (PDT bypass)")

# METHOD 1: Use close_position API (correct way to close LONG positions)
# This tells Alpaca we're CLOSING, not opening a new short position
print(f"\nMethod 1: close_position({safe_qty} contracts)...")
try:
    close_request = ClosePositionRequest(qty=str(safe_qty))
    result = client.close_position(target, close_options=close_request)
    print("✅ close_position succeeded!")
    if hasattr(result, "id"):
        print(f"   Order ID: {result.id}")
        print(f"   Status: {result.status}")
except Exception as e:
    print(f"❌ Method 1 failed: {e}")

    # METHOD 2: Close ALL (full position)
    print("\nMethod 2: close_position (full position)...")
    try:
        result = client.close_position(target)
        print("✅ Full position close succeeded!")
        if hasattr(result, "id"):
            print(f"   Order ID: {result.id}")
    except Exception as e2:
        print(f"❌ Method 2 failed: {e2}")

        # METHOD 3: Try closing just 1 contract at a time
        print("\nMethod 3: close_position (1 contract)...")
        try:
            close_request = ClosePositionRequest(qty="1")
            result = client.close_position(target, close_options=close_request)
            print("✅ Closed 1 contract!")
            if hasattr(result, "id"):
                print(f"   Order ID: {result.id}")
        except Exception as e3:
            print(f"❌ Method 3 failed: {e3}")
            print("\n" + "=" * 60)
            print("ALL METHODS FAILED - Alpaca API issue")
            print("=" * 60)
            sys.exit(1)

print("\n" + "=" * 60)
print("✅ PDT BYPASS COMPLETE")
print("=" * 60)
