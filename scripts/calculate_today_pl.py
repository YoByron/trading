import json


def calculate_pl():
    log_file = "data/audit_trail/hybrid_funnel_runs.jsonl"
    from datetime import datetime

    today_str = datetime.now().strftime("%Y-%m-%d")
    # Optional: Override for testing
    # today_str = "2025-12-09"

    # total_pl = 0.0  # Unused
    trades_count = 0
    winners = 0
    losers = 0

    print(f"Analyzing P/L for {today_str}...")

    try:
        with open(log_file) as f:
            for line in f:
                try:
                    entry = json.loads(line)
                    if (
                        entry.get("ts", "").startswith(today_str)
                        and entry.get("event") == "position.exit"
                    ):
                        payload = entry.get("payload", {})
                        ticker = entry.get("ticker")

                        entry_price = payload.get("entry_price", 0)
                        exit_price = payload.get("exit_price", 0)
                        # pl_pct = payload.get("pl_pct", 0) # Unused
                        reason = payload.get("reason", "unknown")

                        # Calculate pct change manually to verify
                        calc_pct = (
                            ((exit_price - entry_price) / entry_price) * 100 if entry_price else 0
                        )

                        print(
                            f"  {ticker}: {reason.upper()} | Entry: {entry_price:.2f} -> Exit: {exit_price:.2f} | Change: {calc_pct:.2f}%"
                        )

                        trades_count += 1
                        if exit_price > entry_price:
                            winners += 1
                        else:
                            losers += 1

                except json.JSONDecodeError:
                    continue

    except FileNotFoundError:
        print("Log file not found.")
        return

    print("-" * 30)
    print(f"Total Closed Trades: {trades_count}")
    print(f"Winners: {winners}")
    print(f"Losers: {losers}")

    # Also check for BIL sweep (entry)
    print("\nNew Positions (Entries):")
    try:
        with open(log_file) as f:
            for line in f:
                entry = json.loads(line)
                if (
                    entry.get("ts", "").startswith(today_str)
                    and entry.get("event") == "dca.safe_sweep"
                    and entry.get("status") == "executed"
                ):
                    payload = entry.get("payload", {})
                    amount = payload.get("amount", 0)
                    ticker = entry.get("ticker")
                    print(f"  {ticker} Sweep: ${amount:.2f}")
    except:
        pass


if __name__ == "__main__":
    calculate_pl()
