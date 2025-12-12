import json
from datetime import datetime
from pathlib import Path

from alpaca.trading.enums import QueryOrderStatus
from alpaca.trading.requests import GetOrdersRequest
from dotenv import load_dotenv
from src.core.alpaca_trader import AlpacaTrader


def main():
    load_dotenv()
    print("🔄 Syncing Alpaca trades to Dashboard Ledger...")
    trader = AlpacaTrader(paper=True)

    # Fetch today's closed orders
    today = datetime.now().date()
    today_str = today.isoformat()

    # Get all closed orders via Request object
    req = GetOrdersRequest(status=QueryOrderStatus.CLOSED, limit=100)
    closed_orders = trader.trading_client.get_orders(filter=req)

    # Filter for today
    todays_trades = []
    for order in closed_orders:
        if order.filled_at and order.filled_at.date() == today:
            todays_trades.append(order)

    print(f"✅ Found {len(todays_trades)} trades from today.")

    trade_records = []
    for order in todays_trades:
        # Calculate amount
        qty = float(order.filled_qty)
        price = float(order.filled_avg_price) if order.filled_avg_price else 0.0
        amount = qty * price

        record = {
            "symbol": order.symbol,
            "action": order.side.upper(),
            "amount": amount,
            "quantity": qty,
            "price": price,
            "timestamp": order.filled_at.isoformat(),
            "status": "FILLED",
            "strategy": "RiskManager" if "stop" in str(order.type) else "Manual/Orchestrator",
            "reason": "Synced from Alpaca",
            "mode": "PAPER",
        }
        trade_records.append(record)

    # Write to JSON
    file_path = Path(f"data/trades_{today_str}.json")
    with open(file_path, "w") as f:
        json.dump(trade_records, f, indent=4)

    print(f"💾 Saved {len(trade_records)} trades to {file_path}")
    print("👉 Please refresh your dashboard now.")


if __name__ == "__main__":
    main()
