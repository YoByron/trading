#!/usr/bin/env python3
"""Last resort - close via limit order at 0.01."""
import os
import sys
from datetime import datetime

api_key = os.environ.get("ALPACA_API_KEY") or os.environ.get("ALPACA_PAPER_TRADING_5K_API_KEY")
api_secret = os.environ.get("ALPACA_SECRET_KEY") or os.environ.get("ALPACA_PAPER_TRADING_5K_API_SECRET")

if not api_key or not api_secret:
    print("ERROR: Missing Alpaca API credentials")
    sys.exit(1)

from alpaca.trading.client import TradingClient
from alpaca.trading.enums import OrderSide, TimeInForce
from alpaca.trading.requests import LimitOrderRequest

print("=" * 60)
print(f"EMERGENCY CLOSE - LAST RESORT - {datetime.now()}")
print("=" * 60)

client = TradingClient(api_key, api_secret, paper=True)
account = client.get_account()
print(f"\nEquity: ${float(account.equity):,.2f}")
print(f"Options Buying Power: ${float(account.options_buying_power):,.2f}")

target = "SPY260220P00658000"

# Get position
positions = client.get_all_positions()
target_pos = None
for p in positions:
    if p.symbol == target:
        target_pos = p
        qty = int(float(p.qty))
        price = float(p.current_price)
        print(f"\nPosition: {target}")
        print(f"  Qty: {qty}")
        print(f"  Price: ${price:.2f}")
        print(f"  P/L: ${float(p.unrealized_pl):+,.2f}")
        break

if not target_pos:
    print(f"\n{target} not found")
    sys.exit(0)

# Try limit order at current price - slightly below to ensure fill
limit_price = round(price * 0.95, 2)  # 5% below current
print(f"\nTrying limit sell at ${limit_price:.2f}...")

try:
    order = client.submit_order(
        LimitOrderRequest(
            symbol=target,
            qty=qty,
            side=OrderSide.SELL,
            time_in_force=TimeInForce.DAY,
            limit_price=limit_price
        )
    )
    print(f"✅ Order submitted: {order.id}")
    print(f"   Status: {order.status}")
except Exception as e:
    print(f"❌ Limit order failed: {e}")
    
    # Try even lower price
    print(f"\nTrying limit sell at $0.01...")
    try:
        order = client.submit_order(
            LimitOrderRequest(
                symbol=target,
                qty=qty,
                side=OrderSide.SELL,
                time_in_force=TimeInForce.DAY,
                limit_price=0.01
            )
        )
        print(f"✅ Order submitted: {order.id}")
    except Exception as e2:
        print(f"❌ Failed: {e2}")
        
        # Final attempt - close 1 contract only
        print(f"\nTrying to close just 1 contract...")
        try:
            order = client.submit_order(
                LimitOrderRequest(
                    symbol=target,
                    qty=1,
                    side=OrderSide.SELL,
                    time_in_force=TimeInForce.DAY,
                    limit_price=0.01
                )
            )
            print(f"✅ Closed 1 contract: {order.id}")
        except Exception as e3:
            print(f"❌ All attempts failed: {e3}")
            print("\n⚠️ BROKER RESTRICTION - CANNOT CLOSE VIA API")
            sys.exit(1)

print("\nDONE")
