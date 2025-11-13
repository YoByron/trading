#!/usr/bin/env python3
"""
MANUAL TRADE ENTRY TOOL
Allows CEO to log manual trades from SoFi (Tier 3 IPOs) and Crowdfunding platforms (Tier 4)
"""
import json
import sys
from datetime import datetime, date
from pathlib import Path
from typing import Dict, Any, Optional

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

DATA_DIR = Path("data")
STATE_FILE = DATA_DIR / "system_state.json"
MANUAL_TRADES_FILE = DATA_DIR / "manual_trades.json"

# Platform definitions
PLATFORMS = {
    "sofi": {
        "name": "SoFi",
        "tiers": ["tier3"],
        "asset_types": ["IPO", "stock"],
    },
    "wefunder": {
        "name": "Wefunder",
        "tiers": ["tier4"],
        "asset_types": ["crowdfunding"],
    },
    "republic": {
        "name": "Republic",
        "tiers": ["tier4"],
        "asset_types": ["crowdfunding"],
    },
    "startengine": {
        "name": "StartEngine",
        "tiers": ["tier4"],
        "asset_types": ["crowdfunding"],
    },
}

# Tier budget limits
TIER_BUDGETS = {
    "tier3": 1.0,  # $1/day for IPOs
    "tier4": 1.0,  # $1/day for crowdfunding
}


class ManualTradeEntry:
    """Handles manual trade entry for SoFi and crowdfunding platforms"""

    def __init__(self):
        self.state = self.load_state()
        self.manual_trades = self.load_manual_trades()

    def load_state(self) -> Dict[str, Any]:
        """Load system state"""
        if STATE_FILE.exists():
            with open(STATE_FILE, "r") as f:
                return json.load(f)
        raise FileNotFoundError(f"System state not found: {STATE_FILE}")

    def load_manual_trades(self) -> Dict[str, Any]:
        """Load manual trades log"""
        if MANUAL_TRADES_FILE.exists():
            with open(MANUAL_TRADES_FILE, "r") as f:
                return json.load(f)
        return {"trades": [], "positions": []}

    def save_state(self):
        """Save system state"""
        with open(STATE_FILE, "w") as f:
            json.dump(self.state, f, indent=2)

    def save_manual_trades(self):
        """Save manual trades log"""
        with open(MANUAL_TRADES_FILE, "w") as f:
            json.dump(self.manual_trades, f, indent=2)

    def get_today_spending(self, tier: str) -> float:
        """Get total spending for a tier today"""
        today_str = date.today().isoformat()
        total = 0.0
        for trade in self.manual_trades.get("trades", []):
            if trade["tier"] == tier and trade["date"] == today_str and trade["action"] == "buy":
                total += trade["total_cost"]
        return total

    def validate_trade(self, platform: str, tier: str, action: str, symbol: str, quantity: float, price: float, trade_date: str) -> tuple[bool, str]:
        """Validate trade before recording"""

        # Validate platform
        if platform not in PLATFORMS:
            return False, f"Invalid platform: {platform}. Valid: {list(PLATFORMS.keys())}"

        # Validate tier for platform
        if tier not in PLATFORMS[platform]["tiers"]:
            return False, f"{PLATFORMS[platform]['name']} only supports tiers: {PLATFORMS[platform]['tiers']}"

        # Validate action
        if action not in ["buy", "sell"]:
            return False, f"Invalid action: {action}. Must be 'buy' or 'sell'"

        # Validate values
        if quantity <= 0:
            return False, "Quantity must be positive"
        if price <= 0:
            return False, "Price must be positive"

        # Validate date
        try:
            trade_date_obj = date.fromisoformat(trade_date)
            if trade_date_obj > date.today():
                return False, "Cannot record future trades"
        except ValueError:
            return False, f"Invalid date format: {trade_date}. Use YYYY-MM-DD"

        # Validate tier budget (for buys only)
        if action == "buy":
            total_cost = quantity * price
            today_spending = self.get_today_spending(tier)
            tier_budget = TIER_BUDGETS.get(tier, 0)

            # Allow override with warning if exceeds budget
            if today_spending + total_cost > tier_budget:
                print(f"\n⚠️  WARNING: This trade (${total_cost:.2f}) + today's spending (${today_spending:.2f}) = ${today_spending + total_cost:.2f}")
                print(f"⚠️  This exceeds {tier.upper()} daily budget of ${tier_budget:.2f}")
                confirm = input("⚠️  Proceed anyway? [y/N]: ").strip().lower()
                if confirm != 'y':
                    return False, "Trade cancelled by user"

        return True, "Valid"

    def record_trade(self, platform: str, tier: str, action: str, symbol: str, quantity: float, price: float, trade_date: str, notes: str = ""):
        """Record a manual trade"""

        # Validate trade
        valid, message = self.validate_trade(platform, tier, action, symbol, quantity, price, trade_date)
        if not valid:
            raise ValueError(f"Invalid trade: {message}")

        # Calculate totals
        total_cost = quantity * price

        # Create trade record
        trade = {
            "id": f"{platform}_{trade_date}_{symbol}_{datetime.now().timestamp()}",
            "platform": platform,
            "tier": tier,
            "action": action,
            "symbol": symbol,
            "quantity": quantity,
            "price": price,
            "total_cost": total_cost,
            "date": trade_date,
            "recorded_at": datetime.now().isoformat(),
            "notes": notes,
        }

        # Add to manual trades log
        self.manual_trades.setdefault("trades", []).append(trade)

        # Update or create position
        self.update_position(platform, tier, symbol, action, quantity, price)

        # Update system state
        self.update_system_state(tier, action, total_cost)

        # Save everything
        self.save_manual_trades()
        self.save_state()

        print(f"\n✅ Trade recorded successfully!")
        print(f"   Platform: {PLATFORMS[platform]['name']}")
        print(f"   Tier: {tier.upper()}")
        print(f"   Action: {action.upper()}")
        print(f"   Symbol: {symbol}")
        print(f"   Quantity: {quantity}")
        print(f"   Price: ${price:.2f}")
        print(f"   Total: ${total_cost:.2f}")
        print(f"   Date: {trade_date}")

    def update_position(self, platform: str, tier: str, symbol: str, action: str, quantity: float, price: float):
        """Update position tracking"""
        positions = self.manual_trades.setdefault("positions", [])

        # Find existing position
        position = None
        for p in positions:
            if p["platform"] == platform and p["symbol"] == symbol:
                position = p
                break

        if action == "buy":
            if position:
                # Update existing position (average cost)
                total_quantity = position["quantity"] + quantity
                total_cost = (position["quantity"] * position["avg_price"]) + (quantity * price)
                position["quantity"] = total_quantity
                position["avg_price"] = total_cost / total_quantity
                position["last_updated"] = datetime.now().isoformat()
            else:
                # Create new position
                positions.append({
                    "platform": platform,
                    "tier": tier,
                    "symbol": symbol,
                    "quantity": quantity,
                    "avg_price": price,
                    "current_price": price,  # CEO updates manually
                    "unrealized_pl": 0.0,
                    "opened_at": datetime.now().isoformat(),
                    "last_updated": datetime.now().isoformat(),
                })

        elif action == "sell":
            if not position:
                raise ValueError(f"Cannot sell {symbol} - no position exists")
            if position["quantity"] < quantity:
                raise ValueError(f"Cannot sell {quantity} shares of {symbol} - only {position['quantity']} available")

            position["quantity"] -= quantity
            position["last_updated"] = datetime.now().isoformat()

            # Remove position if fully sold
            if position["quantity"] == 0:
                positions.remove(position)

    def update_system_state(self, tier: str, action: str, amount: float):
        """Update system state with manual trade"""

        # Initialize platforms section if doesn't exist
        if "platforms" not in self.state:
            self.state["platforms"] = {
                "alpaca": {
                    "tiers": ["tier1", "tier2"],
                    "equity": self.state["account"]["current_equity"],
                    "trades": self.state["performance"]["total_trades"],
                },
                "manual": {
                    "tiers": ["tier3", "tier4"],
                    "equity": 0.0,
                    "trades": 0,
                },
            }

        # Update manual platform stats
        if action == "buy":
            self.state["platforms"]["manual"]["equity"] += amount
            self.state["platforms"]["manual"]["trades"] += 1

            # Update tier reserves
            if tier == "tier3":
                self.state["investments"]["tier3_reserve"] = self.state["investments"].get("tier3_reserve", 0.0) + amount
            elif tier == "tier4":
                self.state["investments"]["tier4_reserve"] = self.state["investments"].get("tier4_reserve", 0.0) + amount

            # Update total invested
            self.state["investments"]["total_invested"] = self.state["investments"].get("total_invested", 0.0) + amount

        # Add note to system state
        note = f"Manual trade: {tier.upper()} - {action.upper()} ${amount:.2f}"
        self.state.setdefault("notes", []).append(f"[{datetime.now().strftime('%Y-%m-%d %H:%M')}] {note}")

        # Keep last 100 notes
        if len(self.state["notes"]) > 100:
            self.state["notes"] = self.state["notes"][-100:]

    def interactive_entry(self):
        """Interactive CLI for trade entry"""
        print("\n" + "="*70)
        print("MANUAL TRADE ENTRY - SoFi (Tier 3) & Crowdfunding (Tier 4)")
        print("="*70)

        # Select platform
        print("\nAvailable platforms:")
        for key, platform in PLATFORMS.items():
            print(f"  {key:<12} - {platform['name']:<15} (Tiers: {', '.join(platform['tiers'])})")

        platform = input("\nSelect platform: ").strip().lower()
        if platform not in PLATFORMS:
            print(f"❌ Invalid platform: {platform}")
            return

        # Select tier
        valid_tiers = PLATFORMS[platform]["tiers"]
        if len(valid_tiers) == 1:
            tier = valid_tiers[0]
            print(f"Tier: {tier.upper()} (${TIER_BUDGETS[tier]}/day budget)")
        else:
            print(f"\nValid tiers for {PLATFORMS[platform]['name']}: {', '.join(valid_tiers)}")
            tier = input("Select tier: ").strip().lower()
            if tier not in valid_tiers:
                print(f"❌ Invalid tier: {tier}")
                return

        # Select action
        action = input("\nAction (buy/sell): ").strip().lower()
        if action not in ["buy", "sell"]:
            print(f"❌ Invalid action: {action}")
            return

        # Get symbol
        symbol = input("Symbol/Company: ").strip().upper()
        if not symbol:
            print("❌ Symbol required")
            return

        # Get quantity
        try:
            quantity = float(input("Quantity: ").strip())
            if quantity <= 0:
                print("❌ Quantity must be positive")
                return
        except ValueError:
            print("❌ Invalid quantity")
            return

        # Get price
        try:
            price = float(input("Price per share: $").strip())
            if price <= 0:
                print("❌ Price must be positive")
                return
        except ValueError:
            print("❌ Invalid price")
            return

        # Get date
        trade_date_input = input("Date (YYYY-MM-DD or 'today'): ").strip().lower()
        if trade_date_input == 'today' or not trade_date_input:
            trade_date = date.today().isoformat()
        else:
            trade_date = trade_date_input

        # Get notes
        notes = input("Notes (optional): ").strip()

        # Confirm
        total_cost = quantity * price
        print("\n" + "-"*70)
        print("TRADE SUMMARY")
        print("-"*70)
        print(f"Platform:  {PLATFORMS[platform]['name']}")
        print(f"Tier:      {tier.upper()}")
        print(f"Action:    {action.upper()}")
        print(f"Symbol:    {symbol}")
        print(f"Quantity:  {quantity}")
        print(f"Price:     ${price:.2f}")
        print(f"Total:     ${total_cost:.2f}")
        print(f"Date:      {trade_date}")
        if notes:
            print(f"Notes:     {notes}")
        print("-"*70)

        confirm = input("\nConfirm trade? [y/N]: ").strip().lower()
        if confirm != 'y':
            print("❌ Trade cancelled")
            return

        # Record trade
        try:
            self.record_trade(platform, tier, action, symbol, quantity, price, trade_date, notes)
        except Exception as e:
            print(f"\n❌ Error recording trade: {e}")

    def show_positions(self):
        """Show current manual positions"""
        positions = self.manual_trades.get("positions", [])

        if not positions:
            print("\n📊 No manual positions")
            return

        print("\n" + "="*70)
        print("MANUAL POSITIONS (SoFi + Crowdfunding)")
        print("="*70)

        for pos in positions:
            platform_name = PLATFORMS[pos["platform"]]["name"]
            total_value = pos["quantity"] * pos["current_price"]
            total_cost = pos["quantity"] * pos["avg_price"]
            pl = total_value - total_cost
            pl_pct = (pl / total_cost * 100) if total_cost > 0 else 0

            status = "✅" if pl > 0 else "❌" if pl < 0 else "➖"

            print(f"\n{status} {pos['symbol']} ({platform_name} - {pos['tier'].upper()})")
            print(f"   Quantity:      {pos['quantity']}")
            print(f"   Avg Price:     ${pos['avg_price']:.2f}")
            print(f"   Current Price: ${pos['current_price']:.2f}")
            print(f"   Total Value:   ${total_value:.2f}")
            print(f"   Total Cost:    ${total_cost:.2f}")
            print(f"   P/L:           ${pl:+.2f} ({pl_pct:+.2f}%)")

        print("="*70)


def main():
    """Main entry point"""
    if len(sys.argv) > 1 and sys.argv[1] == "positions":
        entry = ManualTradeEntry()
        entry.show_positions()
    else:
        entry = ManualTradeEntry()
        entry.interactive_entry()


if __name__ == "__main__":
    main()
