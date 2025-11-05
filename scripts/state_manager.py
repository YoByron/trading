#!/usr/bin/env python3
"""
STATE MANAGER
Persistent memory system that survives reboots
Tracks all heuristics, profits, trades, and system state
"""
import json
from datetime import datetime, date
from pathlib import Path
from typing import Dict, Any, List

DATA_DIR = Path("data")
STATE_FILE = DATA_DIR / "system_state.json"
DATA_DIR.mkdir(exist_ok=True)


class StateManager:
    """
    Manages all system state with persistence
    Designed to survive reboots and provide continuity
    """

    def __init__(self):
        self.state = self.load_state()

    def load_state(self) -> Dict[str, Any]:
        """Load state from disk or create new"""
        if STATE_FILE.exists():
            with open(STATE_FILE, "r") as f:
                state = json.load(f)

            # CRITICAL: Add staleness metadata and evaluate quality
            state = self._add_staleness_metadata(state)

            # CRITICAL: Evaluate state quality and print warnings
            evaluation = self._evaluate_state_quality(state)

            # BLOCK if EXPIRED (>7 days old)
            if state["meta"]["staleness_status"] == "EXPIRED":
                error_msg = f"""
╔════════════════════════════════════════════════════════════════╗
║  CRITICAL ERROR: STATE DATA EXPIRED                            ║
╚════════════════════════════════════════════════════════════════╝

State last updated: {state['meta']['last_updated']}
Staleness: {state['meta']['staleness_hours']:.1f} hours ({state['meta']['staleness_hours']/24:.1f} days)
Status: {state['meta']['staleness_status']}

⛔ REFUSING TO LOAD EXPIRED DATA ⛔

This prevents hallucinations where the system reports old data as current.

ACTION REQUIRED:
1. Run daily_checkin.py to refresh state with current data
2. Or manually update system_state.json with current account data
"""
                raise ValueError(error_msg)

            return state
        return self._create_initial_state()

    def save_state(self):
        """Persist state to disk"""
        self.state["meta"]["last_updated"] = datetime.now().isoformat()

        # Clear staleness metadata when saving fresh data
        if "last_loaded" in self.state["meta"]:
            del self.state["meta"]["last_loaded"]
        if "staleness_hours" in self.state["meta"]:
            del self.state["meta"]["staleness_hours"]
        if "staleness_status" in self.state["meta"]:
            del self.state["meta"]["staleness_status"]
        if "self_evaluation" in self.state["meta"]:
            del self.state["meta"]["self_evaluation"]

        with open(STATE_FILE, "w") as f:
            json.dump(self.state, f, indent=2)

    def _create_initial_state(self) -> Dict[str, Any]:
        """Create initial state structure"""
        return {
            "meta": {
                "version": "1.0",
                "created": datetime.now().isoformat(),
                "last_updated": datetime.now().isoformat(),
            },
            "challenge": {
                "start_date": date.today().isoformat(),
                "current_day": 1,
                "total_days": 30,
                "status": "active",
            },
            "account": {
                "starting_balance": 100000.0,
                "current_equity": 100000.0,
                "cash": 100000.0,
                "positions_value": 0.0,
                "total_pl": 0.0,
                "total_pl_pct": 0.0,
            },
            "investments": {
                "total_invested": 0.0,
                "tier1_invested": 0.0,
                "tier2_invested": 0.0,
                "tier3_reserve": 0.0,
                "tier4_reserve": 0.0,
            },
            "performance": {
                "total_trades": 0,
                "winning_trades": 0,
                "losing_trades": 0,
                "win_rate": 0.0,
                "best_trade": None,
                "worst_trade": None,
                "avg_return": 0.0,
            },
            "strategies": {
                "tier1": {
                    "name": "Core ETF Strategy",
                    "allocation": 0.6,
                    "daily_amount": 6.0,
                    "trades_executed": 0,
                    "total_invested": 0.0,
                    "status": "active",
                },
                "tier2": {
                    "name": "Growth Stock Strategy",
                    "allocation": 0.2,
                    "daily_amount": 2.0,
                    "trades_executed": 0,
                    "total_invested": 0.0,
                    "status": "active",
                },
                "tier3": {
                    "name": "IPO Strategy",
                    "allocation": 0.1,
                    "daily_amount": 1.0,
                    "reserve_balance": 0.0,
                    "status": "tracking",
                },
                "tier4": {
                    "name": "Crowdfunding Strategy",
                    "allocation": 0.1,
                    "daily_amount": 1.0,
                    "reserve_balance": 0.0,
                    "status": "tracking",
                },
            },
            "heuristics": {
                "best_performing_etf": None,
                "best_performing_stock": None,
                "avg_daily_return": 0.0,
                "max_drawdown": 0.0,
                "sharpe_ratio": 0.0,
                "volatility": 0.0,
                "winning_symbols": [],
                "losing_symbols": [],
            },
            "automation": {
                "cron_enabled": False,
                "last_execution": None,
                "next_execution": None,
                "execution_count": 0,
                "failures": 0,
            },
            "video_analysis": {
                "enabled": True,
                "videos_analyzed": 0,
                "stocks_added_from_videos": 0,
                "last_analysis_date": None,
                "video_sources": [],
                "watchlist_additions": [],
            },
            "notes": [],
        }

    def update_challenge_day(self):
        """Update current day of challenge"""
        start = datetime.fromisoformat(self.state["challenge"]["start_date"]).date()
        today = date.today()
        day = (today - start).days + 1
        self.state["challenge"]["current_day"] = day
        self.save_state()

    def record_trade(self, tier: str, symbol: str, amount: float, order_id: str):
        """Record a trade execution"""
        # Update strategy stats
        if tier in ["tier1", "tier2"]:
            self.state["strategies"][tier]["trades_executed"] += 1
            self.state["strategies"][tier]["total_invested"] += amount

        # Update investments
        self.state["investments"]["total_invested"] += amount
        if tier == "tier1":
            self.state["investments"]["tier1_invested"] += amount
        elif tier == "tier2":
            self.state["investments"]["tier2_invested"] += amount

        # Update performance
        self.state["performance"]["total_trades"] += 1

        # Add note
        self.add_note(f"Trade executed: {tier.upper()} - {symbol} ${amount}")

        self.save_state()

    def update_account(self, equity: float, cash: float, pl: float, pl_pct: float):
        """Update account information"""
        self.state["account"]["current_equity"] = equity
        self.state["account"]["cash"] = cash
        self.state["account"]["positions_value"] = equity - cash
        self.state["account"]["total_pl"] = pl
        self.state["account"]["total_pl_pct"] = pl_pct
        self.save_state()

    def update_heuristics(self, **kwargs):
        """Update heuristic data"""
        for key, value in kwargs.items():
            if key in self.state["heuristics"]:
                self.state["heuristics"][key] = value
        self.save_state()

    def add_note(self, note: str):
        """Add a note to system log"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
        self.state["notes"].append(f"[{timestamp}] {note}")
        # Keep last 100 notes
        if len(self.state["notes"]) > 100:
            self.state["notes"] = self.state["notes"][-100:]
        self.save_state()

    def record_video_analysis(self, video_title: str, analyst: str, stocks_added: List[str]):
        """Record a YouTube video analysis"""
        if "video_analysis" not in self.state:
            self.state["video_analysis"] = {
                "enabled": True,
                "videos_analyzed": 0,
                "stocks_added_from_videos": 0,
                "last_analysis_date": None,
                "video_sources": [],
                "watchlist_additions": [],
            }

        self.state["video_analysis"]["videos_analyzed"] += 1
        self.state["video_analysis"]["stocks_added_from_videos"] += len(stocks_added)
        self.state["video_analysis"]["last_analysis_date"] = datetime.now().isoformat()

        # Add to video sources (keep last 20)
        video_entry = {
            "title": video_title,
            "analyst": analyst,
            "date": datetime.now().isoformat(),
            "stocks_added": stocks_added,
        }
        self.state["video_analysis"]["video_sources"].append(video_entry)
        if len(self.state["video_analysis"]["video_sources"]) > 20:
            self.state["video_analysis"]["video_sources"] = self.state["video_analysis"]["video_sources"][-20:]

        # Add to watchlist additions
        for ticker in stocks_added:
            self.state["video_analysis"]["watchlist_additions"].append({
                "ticker": ticker,
                "source": f"{analyst} - {video_title}",
                "date_added": datetime.now().isoformat(),
            })

        self.add_note(f"Video analysis: {analyst} - {len(stocks_added)} stocks added to watchlist")
        self.save_state()

    def get_summary(self) -> Dict[str, Any]:
        """Get current state summary"""
        return {
            "day": self.state["challenge"]["current_day"],
            "equity": self.state["account"]["current_equity"],
            "pl": self.state["account"]["total_pl"],
            "pl_pct": self.state["account"]["total_pl_pct"],
            "trades": self.state["performance"]["total_trades"],
            "invested": self.state["investments"]["total_invested"],
        }

    def _add_staleness_metadata(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Add staleness metadata to state"""
        now = datetime.now()
        last_updated = datetime.fromisoformat(state["meta"]["last_updated"])

        staleness_hours = (now - last_updated).total_seconds() / 3600

        # Determine staleness status
        # STRICT thresholds to prevent hallucinations
        if staleness_hours < 24:
            status = "FRESH"
        elif staleness_hours < 48:
            status = "AGING"
        elif staleness_hours < 72:  # 3 days
            status = "STALE"
        else:  # >3 days
            status = "EXPIRED"

        state["meta"]["last_loaded"] = now.isoformat()
        state["meta"]["staleness_hours"] = staleness_hours
        state["meta"]["staleness_status"] = status

        return state

    def _evaluate_state_quality(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Self-evaluate state quality and staleness
        PRINTS WARNINGS to console
        Returns evaluation dict
        """
        warnings = []
        recommendations = []

        staleness_hours = state["meta"]["staleness_hours"]
        staleness_days = staleness_hours / 24
        status = state["meta"]["staleness_status"]

        # Generate warnings based on staleness
        if status == "FRESH":
            confidence = 0.95
        elif status == "AGING":
            confidence = 0.70
            warnings.append(f"State is {staleness_days:.1f} days old - account balance may not reflect recent trades")
            recommendations.append("Run daily_checkin.py to refresh state")
        elif status == "STALE":
            confidence = 0.30
            warnings.append(f"State is {staleness_days:.1f} days old - HIGH RISK of using stale data")
            warnings.append("Account balance not updated in several days - may not reflect current positions")
            recommendations.append("URGENT: Run daily_checkin.py to refresh state")
        else:  # EXPIRED
            confidence = 0.05
            warnings.append(f"State is {staleness_days:.1f} days old - CRITICAL STALENESS")
            warnings.append("Data is severely outdated and CANNOT be trusted")
            warnings.append("Using this data WILL cause hallucinations")
            recommendations.append("REQUIRED: Run daily_checkin.py immediately")

        # Check if challenge day calculation would be wrong
        if staleness_days >= 1:
            warnings.append(f"Challenge day calculation may be off by {int(staleness_days)} days")

        evaluation = {
            "warnings": warnings,
            "recommendations": recommendations,
            "confidence_in_state": confidence,
            "staleness_hours": staleness_hours,
            "staleness_days": staleness_days,
            "status": status
        }

        state["meta"]["self_evaluation"] = evaluation

        # PRINT WARNINGS TO CONSOLE
        if status != "FRESH":
            print("\n" + "="*70)
            print(f"⚠️  SYSTEM STATE WARNINGS ⚠️  [{status}]")
            print("="*70)
            for warning in warnings:
                print(f"  ⚠️  {warning}")
            print()
            print("RECOMMENDATIONS:")
            for rec in recommendations:
                print(f"  → {rec}")
            print()
            print(f"Confidence in state: {confidence*100:.0f}% ", end="")
            if confidence < 0.3:
                print("(VERY LOW)")
            elif confidence < 0.7:
                print("(LOW)")
            else:
                print("(MODERATE)")
            print("="*70)
            print()

        return evaluation

    def export_for_context(self) -> str:
        """Export state as context for Claude memory"""
        summary = self.get_summary()

        # Include staleness warning in context
        staleness_warning = ""
        if "self_evaluation" in self.state["meta"]:
            eval_data = self.state["meta"]["self_evaluation"]
            if eval_data["status"] != "FRESH":
                staleness_warning = f"""
⚠️  DATA STALENESS WARNING ⚠️
Status: {eval_data['status']}
Age: {eval_data['staleness_days']:.1f} days
Confidence: {eval_data['confidence_in_state']*100:.0f}%
Warnings: {len(eval_data['warnings'])} issues detected
"""

        context = f"""
TRADING SYSTEM STATE (Day {summary['day']}/30)
{staleness_warning}
ACCOUNT:
- Equity: ${summary['equity']:,.2f}
- P/L: ${summary['pl']:+,.2f} ({summary['pl_pct']:+.2f}%)
- Total Invested: ${summary['invested']:.2f}
- Total Trades: {summary['trades']}

STRATEGIES:
- Tier 1 (Core ETF): {self.state['strategies']['tier1']['trades_executed']} trades
- Tier 2 (Growth): {self.state['strategies']['tier2']['trades_executed']} trades
- Tier 3 (IPO): ${self.state['strategies']['tier3']['reserve_balance']:.2f} reserved
- Tier 4 (Crowdfunding): ${self.state['strategies']['tier4']['reserve_balance']:.2f} reserved

HEURISTICS:
- Best ETF: {self.state['heuristics']['best_performing_etf']}
- Avg Daily Return: {self.state['heuristics']['avg_daily_return']:.2f}%
- Max Drawdown: {self.state['heuristics']['max_drawdown']:.2f}%

RECENT NOTES:
{chr(10).join(self.state['notes'][-5:])}
"""
        return context


def main():
    """Test state manager"""
    sm = StateManager()

    print("=== SYSTEM STATE ===")
    print(json.dumps(sm.get_summary(), indent=2))

    print("\n=== CONTEXT FOR CLAUDE ===")
    print(sm.export_for_context())


if __name__ == "__main__":
    main()
