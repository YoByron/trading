import os
import sys
from datetime import datetime

import pandas as pd
from dotenv import load_dotenv

# Add project root to path
sys.path.append(os.getcwd())

import alpaca_trade_api as tradeapi
from src.brokers.kalshi_client import get_kalshi_client
from src.brokers.tradier_client import get_tradier_client

# Load env
load_dotenv()

DASHBOARD_PATH = "dashboard.md"


def fetch_holdings():
    positions = []

    # 1. Alpaca
    try:
        is_paper = os.getenv("ALPACA_PAPER", "true").lower() in ("true", "1", "yes", "on")
        base_url = "https://paper-api.alpaca.markets" if is_paper else "https://api.alpaca.markets"
        api = tradeapi.REST(os.getenv("ALPACA_API_KEY"), os.getenv("ALPACA_SECRET_KEY"), base_url)
        alpaca_positions = api.list_positions()
        for p in alpaca_positions:
            val = float(p.market_value)
            pl = float(p.unrealized_pl)
            pl_pct = float(p.unrealized_plpc) * 100

            icon = "🟢" if pl >= 0 else "🔴"

            positions.append(
                {
                    "Symbol": f"**{p.symbol}**",
                    "Qty": float(p.qty),
                    "Entry Price": f"${float(p.avg_entry_price):.2f}",
                    "Current Price": f"${float(p.current_price):.2f}",
                    "Value": f"${val:,.2f}",
                    "Unrealized P/L": f"{icon} ${pl:+.2f} ({pl_pct:+.2f}%)",
                    "Source": "Alpaca",
                }
            )
    except Exception as e:
        print(f"Alpaca error: {e}")

    # 2. Kalshi
    try:
        is_kalshi_paper = os.getenv("KALSHI_PAPER", "true").lower() in ("true", "1", "yes", "on")
        kalshi = get_kalshi_client(paper=is_kalshi_paper)
        if kalshi.is_configured():
            k_positions = kalshi.get_positions()
            for p in k_positions:
                name = f"{p.market_ticker} ({p.side.upper()})"
                cost = p.cost_basis
                val = p.market_value
                pl = p.unrealized_pl
                pl_pct = (pl / cost * 100) if cost > 0 else 0
                qty = p.quantity
                # Convert cents to dollars
                entry = (cost / qty / 100) if qty > 0 else 0
                current = (val / qty / 100) if qty > 0 else 0

                icon = "🟢" if pl >= 0 else "🔴"

                positions.append(
                    {
                        "Symbol": f"**{name}**",
                        "Qty": qty,
                        "Entry Price": f"${entry:.2f}",
                        "Current Price": f"${current:.2f}",
                        "Value": f"${(val / 100):,.2f}",
                        "Unrealized P/L": f"{icon} ${(pl / 100):+.2f} ({pl_pct:+.2f}%)",
                        "Source": "Kalshi",
                    }
                )
    except Exception as e:
        print(f"Kalshi error: {e}")

    # 3. Tradier
    try:
        is_tradier_paper = os.getenv("TRADIER_PAPER", "true").lower() in ("true", "1", "yes", "on")
        tradier = get_tradier_client(paper=is_tradier_paper)
        if tradier.is_configured():
            t_positions = tradier.get_positions()
            for p in t_positions:
                pl = float(p.unrealized_pl)
                pl_pct = float(p.unrealized_pl_pct)
                icon = "🟢" if pl >= 0 else "🔴"

                positions.append(
                    {
                        "Symbol": f"**{p.symbol}**",
                        "Qty": float(p.quantity),
                        "Entry Price": f"${(p.cost_basis / p.quantity):.2f}"
                        if p.quantity
                        else "$0.00",
                        "Current Price": f"${p.current_price:.2f}",
                        "Value": f"${(p.current_price * p.quantity):,.2f}",
                        "Unrealized P/L": f"{icon} ${pl:+.2f} ({pl_pct:+.2f}%)",
                        "Source": "Tradier",
                    }
                )
    except Exception as e:
        print(f"Tradier error: {e}")

    return positions


def update_dashboard():
    print("Fetching live holdings...")
    positions = fetch_holdings()

    if not positions:
        print("No positions found or error fetching.")
        # Create empty table
        df = pd.DataFrame(
            columns=[
                "Symbol",
                "Source",
                "Qty",
                "Entry Price",
                "Current Price",
                "Value",
                "Unrealized P/L",
            ]
        )
    else:
        df = pd.DataFrame(positions)
        # Reorder columns
        df = df[
            ["Symbol", "Source", "Qty", "Entry Price", "Current Price", "Value", "Unrealized P/L"]
        ]

    # Convert to Markdown
    markdown_table = df.to_markdown(index=False)

    # Read existing dashboard
    with open(DASHBOARD_PATH) as f:
        content = f.read()

    # Identify Holdings Section
    start_marker = "## 💼 Current Holdings"
    end_marker = "## 🚨 CRITICAL ISSUES"

    start_idx = content.find(start_marker)
    end_idx = content.find(end_marker)

    if start_idx == -1 or end_idx == -1:
        print("Could not locate Holdings section in dashboard.md")
        # Fallback: Just print it so user sees we tried
        print(markdown_table)
        return

    # Construct new content
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M ET")

    new_section = f"{start_marker}\n\n*Live Synced: {timestamp}*\n\n{markdown_table}\n\n\n"

    new_content = content[:start_idx] + new_section + content[end_idx:]

    # Update header timestamp too
    header_marker = "**Last Updated**:"
    header_end_line = content.find("\n", content.find(header_marker))
    if header_marker in content:
        # Simple string replacement for the first occurrence
        new_content = new_content.replace(
            content[content.find(header_marker) : header_end_line], f"**Last Updated**: {timestamp}"
        )

    with open(DASHBOARD_PATH, "w") as f:
        f.write(new_content)

    print("Dashboard updated successfully.")


if __name__ == "__main__":
    update_dashboard()
