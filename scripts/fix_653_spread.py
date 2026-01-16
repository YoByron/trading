#!/usr/bin/env python3
"""Fix broken 653/658 spread by selling 1 extra long put."""
import os
import sys

from alpaca.trading.client import TradingClient
from alpaca.trading.requests import MarketOrderRequest
from alpaca.trading.enums import OrderSide, TimeInForce

api_key = os.environ.get("ALPACA_API_KEY") or os.environ.get("ALPACA_PAPER_TRADING_5K_API_KEY")
secret_key = os.environ.get("ALPACA_SECRET_KEY") or os.environ.get("ALPACA_PAPER_TRADING_5K_API_SECRET")

if not api_key or not secret_key:
    print("ERROR: Missing API credentials")
    sys.exit(1)

client = TradingClient(api_key, secret_key, paper=True)

# Get positions
positions = client.get_all_positions()
print("Current positions:")
for pos in positions:
    print("  " + pos.symbol + ": qty=" + str(pos.qty))

# Find target
target = None
for pos in positions:
    if pos.symbol == "SPY260220P00653000":
        target = pos
        break

if not target:
    print("SPY260220P00653000 not found - already fixed or never existed")
    sys.exit(0)

qty = int(float(target.qty))
print("Target: " + target.symbol + " qty=" + str(qty))

if qty <= 1:
    print("Already at 1 or less - spread is balanced")
    sys.exit(0)

# Sell 1 to fix
print("Selling 1 contract to reduce from " + str(qty) + " to " + str(qty-1) + "...")
order = MarketOrderRequest(
    symbol="SPY260220P00653000",
    qty=1,
    side=OrderSide.SELL,
    time_in_force=TimeInForce.DAY
)
result = client.submit_order(order)
print("Order submitted: " + str(result.id))
print("Status: " + str(result.status))
print("Spread should now be balanced (1 long / 1 short)")
