#!/usr/bin/env python3
"""
Automated Profit-Taking

CTO Decision: Take partial profits at +3% to lock in gains.
"""

import os
import json
import sys
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import HTTPError

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

ALPACA_KEY = os.getenv("ALPACA_API_KEY")
ALPACA_SECRET = os.getenv("ALPACA_SECRET_KEY")
ALPACA_BASE_URL = os.getenv("ALPACA_BASE_URL", "https://paper-api.alpaca.markets")

DATA_DIR = Path("data")
SYSTEM_STATE_FILE = DATA_DIR / "system_state.json"

PROFIT_TARGET_PCT = 3.0  # Take profit at +3%
PARTIAL_SELL_PCT = 0.5  # Sell 50% of position


def make_request(url, method="GET", data=None):
    """Make HTTP request."""
    req = Request(url)
    req.add_header("APCA-API-KEY-ID", ALPACA_KEY)
    req.add_header("APCA-API-SECRET-KEY", ALPACA_SECRET)
    req.add_header("Content-Type", "application/json")
    
    if method == "POST" and data:
        req.data = json.dumps(data).encode('utf-8')
        req.get_method = lambda: "POST"
    
    with urlopen(req) as response:
        return json.loads(response.read().decode('utf-8'))


def check_profit_taking_opportunities():
    """Check for positions that have reached profit target."""
    print("=" * 80)
    print("💰 AUTOMATED PROFIT-TAKING")
    print("=" * 80)
    
    if not SYSTEM_STATE_FILE.exists():
        print("System state not found")
        return
    
    with open(SYSTEM_STATE_FILE) as f:
        state = json.load(f)
    
    positions = state.get("performance", {}).get("open_positions", [])
    
    if not positions:
        print("No open positions")
        return
    
    print(f"\n📊 Analyzing {len(positions)} positions for profit-taking...\n")
    
    actions_taken = []
    
    for pos in positions:
        symbol = pos.get("symbol", "UNKNOWN")
        entry_price = pos.get("entry_price", 0)
        current_price = pos.get("current_price", 0)
        quantity = pos.get("quantity", 0)
        unrealized_pl_pct = pos.get("unrealized_pl_pct", 0)
        
        print(f"{symbol}:")
        print(f"  Entry: ${entry_price:.2f}, Current: ${current_price:.2f}")
        print(f"  P/L: {unrealized_pl_pct:+.2f}%")
        
        if unrealized_pl_pct >= PROFIT_TARGET_PCT:
            sell_qty = quantity * PARTIAL_SELL_PCT
            
            print(f"  ✅ Profit target reached (+{unrealized_pl_pct:.2f}%)")
            print(f"  🎯 Selling {sell_qty:.4f} shares (50% of position)")
            
            # Place sell order
            try:
                data = {
                    "symbol": symbol,
                    "qty": round(sell_qty, 4),
                    "side": "sell",
                    "type": "market",
                    "time_in_force": "day",
                }
                
                req = Request(f"{ALPACA_BASE_URL}/v2/orders")
                req.add_header("APCA-API-KEY-ID", ALPACA_KEY)
                req.add_header("APCA-API-SECRET-KEY", ALPACA_SECRET)
                req.add_header("Content-Type", "application/json")
                req.data = json.dumps(data).encode('utf-8')
                req.get_method = lambda: "POST"
                
                with urlopen(req) as response:
                    order = json.loads(response.read().decode('utf-8'))
                    actions_taken.append({
                        "symbol": symbol,
                        "qty_sold": sell_qty,
                        "order_id": order.get("id"),
                    })
                    print(f"  ✅ Profit-taking order placed: {order.get('id')}")
            except Exception as e:
                print(f"  ❌ Failed to place order: {e}")
        else:
            print(f"  ⏳ Not yet at profit target ({PROFIT_TARGET_PCT}%)")
        
        print()
    
    print("=" * 80)
    print("📋 SUMMARY")
    print("=" * 80)
    print(f"Profit-taking orders placed: {len(actions_taken)}")
    for action in actions_taken:
        print(f"  ✅ {action['symbol']}: Sold {action['qty_sold']:.4f} shares")
    
    return actions_taken


if __name__ == "__main__":
    if not ALPACA_KEY or not ALPACA_SECRET:
        print("ERROR: Alpaca credentials not found")
        sys.exit(1)
    
    try:
        check_profit_taking_opportunities()
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

