#!/usr/bin/env python3
"""Close positions opened BEFORE today to bypass PDT."""
import os
import sys
from datetime import datetime, timezone

api_key = os.environ.get("ALPACA_API_KEY") or os.environ.get("ALPACA_PAPER_TRADING_5K_API_KEY")
api_secret = os.environ.get("ALPACA_SECRET_KEY") or os.environ.get("ALPACA_PAPER_TRADING_5K_API_SECRET")

if not api_key or not api_secret:
    print("ERROR: Missing Alpaca API credentials")
    sys.exit(1)

from alpaca.trading.client import TradingClient
from alpaca.trading.enums import OrderSide, TimeInForce, QueryOrderStatus
from alpaca.trading.requests import MarketOrderRequest, GetOrdersRequest

print("=" * 60)
print(f"CLOSE NON-DAYTRADE POSITIONS - {datetime.now()}")
print("=" * 60)

client = TradingClient(api_key, api_secret, paper=True)
account = client.get_account()
print(f"\nEquity: ${float(account.equity):,.2f}")
print(f"Day Trade Count: {account.daytrade_count}")

target = "SPY260220P00658000"
today = datetime.now(timezone.utc).date()

# Get filled orders using correct API
try:
    request = GetOrdersRequest(status=QueryOrderStatus.ALL, limit=100)
    orders = client.get_orders(filter=request)
except:
    orders = client.get_orders()

buys_today = 0
buys_before = 0

for order in orders:
    if order.symbol == target and order.side.name == 'BUY' and order.filled_at:
        if order.filled_at.date() == today:
            buys_today += int(float(order.filled_qty or 0))
        else:
            buys_before += int(float(order.filled_qty or 0))

print(f"\n{target}: {buys_today} today, {buys_before} before")
safe = buys_before

if safe <= 0:
    print("No safe contracts to close - trying all")
    positions = client.get_all_positions()
    for p in positions:
        if p.symbol == target:
            safe = int(float(p.qty))
            break

if safe <= 0:
    print("Position not found")
    sys.exit(0)

print(f"Closing {safe} contracts...")
try:
    order = client.submit_order(
        MarketOrderRequest(symbol=target, qty=safe, side=OrderSide.SELL, time_in_force=TimeInForce.DAY)
    )
    print(f"✅ Order: {order.id} - {order.status}")
except Exception as e:
    print(f"❌ Failed: {e}")
    sys.exit(1)

print("DONE")
