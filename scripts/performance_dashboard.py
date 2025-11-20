#!/usr/bin/env python3
"""
Performance Analytics and Reporting Dashboard

Generates comprehensive performance analytics including:
- Win rate and Sharpe ratio
- P/L trends over time
- Data source performance metrics
- System reliability metrics
- Position analysis
"""

import os
import sys
import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional
from collections import defaultdict

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from dotenv import load_dotenv
load_dotenv()

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
DATA_DIR = Path("data")
PERF_LOG_FILE = DATA_DIR / "performance_log.json"
SYSTEM_STATE_FILE = DATA_DIR / "system_state.json"


class PerformanceDashboard:
    """Generates performance analytics and reports."""

    def __init__(self):
        self.perf_data: List[Dict] = []
        self.system_state: Dict = {}
        self.load_data()

    def load_data(self):
        """Load performance and system state data."""
        if PERF_LOG_FILE.exists():
            try:
                with open(PERF_LOG_FILE, 'r') as f:
                    self.perf_data = json.load(f)
            except Exception as e:
                logger.error(f"Error loading performance log: {e}")

        if SYSTEM_STATE_FILE.exists():
            try:
                with open(SYSTEM_STATE_FILE, 'r') as f:
                    self.system_state = json.load(f)
            except Exception as e:
                logger.error(f"Error loading system state: {e}")

    def calculate_win_rate(self) -> Dict:
        """Calculate win rate from closed trades."""
        closed_trades = self.system_state.get("closed_trades", [])
        if not closed_trades:
            return {
                "win_rate": 0.0,
                "total_trades": 0,
                "wins": 0,
                "losses": 0
            }

        wins = sum(1 for trade in closed_trades if trade.get("pl", 0) > 0)
        losses = sum(1 for trade in closed_trades if trade.get("pl", 0) <= 0)
        total = len(closed_trades)
        win_rate = (wins / total * 100) if total > 0 else 0.0

        return {
            "win_rate": win_rate,
            "total_trades": total,
            "wins": wins,
            "losses": losses
        }

    def calculate_pl_trends(self, days: int = 30) -> Dict:
        """Calculate P/L trends over time."""
        if not self.perf_data:
            return {}

        # Get last N days
        recent_data = self.perf_data[-days:] if len(self.perf_data) > days else self.perf_data

        daily_pl = []
        cumulative_pl = 0
        for entry in recent_data:
            pl = entry.get("pl", 0)
            cumulative_pl += pl
            daily_pl.append({
                "date": entry.get("date"),
                "pl": pl,
                "cumulative_pl": cumulative_pl,
                "equity": entry.get("equity", 0)
            })

        if not daily_pl:
            return {}

        total_pl = daily_pl[-1]["cumulative_pl"] if daily_pl else 0
        avg_daily_pl = total_pl / len(daily_pl) if daily_pl else 0

        return {
            "total_pl": total_pl,
            "avg_daily_pl": avg_daily_pl,
            "daily_pl": daily_pl,
            "period_days": len(daily_pl)
        }

    def get_data_source_metrics(self) -> Dict:
        """Get data source performance metrics."""
        try:
            from src.utils.market_data import get_market_data_provider
            provider = get_market_data_provider()
            return provider.get_performance_metrics()
        except Exception as e:
            logger.warning(f"Could not fetch data source metrics: {e}")
            return {}

    def get_system_reliability(self) -> Dict:
        """Calculate system reliability metrics."""
        if not self.perf_data:
            return {}

        # Count days with data
        total_days = len(self.perf_data)
        if total_days == 0:
            return {}

        # Check for gaps (days without entries)
        gaps = 0
        if total_days > 1:
            for i in range(1, total_days):
                prev_date = datetime.fromisoformat(self.perf_data[i-1]["date"])
                curr_date = datetime.fromisoformat(self.perf_data[i]["date"])
                days_diff = (curr_date - prev_date).days
                if days_diff > 1:
                    gaps += days_diff - 1

        reliability = ((total_days - gaps) / (total_days + gaps) * 100) if (total_days + gaps) > 0 else 0

        return {
            "total_days_tracked": total_days,
            "data_gaps": gaps,
            "reliability_percent": reliability
        }

    def get_position_analysis(self) -> Dict:
        """Analyze current positions."""
        positions = self.system_state.get("positions", [])
        if not positions:
            return {"total_positions": 0}

        total_value = sum(pos.get("market_value", 0) for pos in positions)
        total_pl = sum(pos.get("unrealized_pl", 0) for pos in positions)
        total_pl_pct = (total_pl / total_value * 100) if total_value > 0 else 0

        return {
            "total_positions": len(positions),
            "total_value": total_value,
            "total_unrealized_pl": total_pl,
            "total_unrealized_pl_pct": total_pl_pct,
            "positions": positions
        }

    def generate_report(self, days: int = 30) -> Dict:
        """Generate comprehensive performance report."""
        win_rate_stats = self.calculate_win_rate()
        pl_trends = self.calculate_pl_trends(days)
        data_source_metrics = self.get_data_source_metrics()
        reliability = self.get_system_reliability()
        position_analysis = self.get_position_analysis()

        return {
            "timestamp": datetime.now().isoformat(),
            "period_days": days,
            "win_rate": win_rate_stats,
            "pl_trends": pl_trends,
            "data_source_metrics": data_source_metrics,
            "system_reliability": reliability,
            "position_analysis": position_analysis
        }

    def print_dashboard(self, report: Dict):
        """Print formatted dashboard."""
        print("\n" + "=" * 70)
        print("PERFORMANCE ANALYTICS DASHBOARD")
        print("=" * 70)
        print(f"Generated: {report['timestamp']}")
        print(f"Period: Last {report['period_days']} days")
        print()

        # Win Rate
        wr = report["win_rate"]
        print("📊 WIN RATE:")
        print(f"   Rate: {wr['win_rate']:.1f}%")
        print(f"   Total Trades: {wr['total_trades']}")
        print(f"   Wins: {wr['wins']} | Losses: {wr['losses']}")
        print()

        # P/L Trends
        pl = report["pl_trends"]
        if pl:
            print("💰 P/L TRENDS:")
            print(f"   Total P/L: ${pl['total_pl']:+,.2f}")
            print(f"   Avg Daily P/L: ${pl['avg_daily_pl']:+,.2f}")
            print(f"   Period: {pl['period_days']} days")
            print()

        # System Reliability
        rel = report["system_reliability"]
        if rel:
            print("🔧 SYSTEM RELIABILITY:")
            print(f"   Reliability: {rel['reliability_percent']:.1f}%")
            print(f"   Days Tracked: {rel['total_days_tracked']}")
            print(f"   Data Gaps: {rel['data_gaps']}")
            print()

        # Data Source Metrics
        dsm = report["data_source_metrics"]
        if dsm:
            print("📡 DATA SOURCE PERFORMANCE:")
            for source, metrics in dsm.items():
                print(f"   {source.upper()}:")
                print(f"      Success Rate: {metrics['success_rate']:.1%}")
                print(f"      Avg Latency: {metrics['avg_latency_ms']:.1f}ms")
                print(f"      Total Requests: {metrics['total_requests']}")
            print()

        # Position Analysis
        pos = report["position_analysis"]
        if pos.get("total_positions", 0) > 0:
            print("📈 POSITION ANALYSIS:")
            print(f"   Total Positions: {pos['total_positions']}")
            print(f"   Total Value: ${pos['total_value']:,.2f}")
            print(f"   Unrealized P/L: ${pos['total_unrealized_pl']:+,.2f} ({pos['total_unrealized_pl_pct']:+.2f}%)")
            print()

        print("=" * 70)


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Generate performance analytics dashboard")
    parser.add_argument(
        "--days",
        type=int,
        default=30,
        help="Number of days to analyze (default: 30)"
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output as JSON instead of formatted text"
    )
    args = parser.parse_args()

    dashboard = PerformanceDashboard()
    report = dashboard.generate_report(args.days)

    if args.json:
        print(json.dumps(report, indent=2))
    else:
        dashboard.print_dashboard(report)


if __name__ == "__main__":
    main()


