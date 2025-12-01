#!/usr/bin/env python3
"""
Test script to verify REIT (VNQ) allocation and execution logic.

This script:
1. Calculates REIT allocation based on current daily investment
2. Verifies allocation exceeds execution threshold ($0.50)
3. Tests the allocation calculation logic
4. Shows what would be executed
"""

import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.strategies.core_strategy import CoreStrategy


def test_reit_allocation():
    """Test REIT allocation calculation."""

    print("=" * 80)
    print("REIT (VNQ) ALLOCATION TEST")
    print("=" * 80)
    print()

    # Get daily investment from environment or use default
    daily_investment = float(os.getenv("DAILY_INVESTMENT", "900.0"))

    print("📊 Configuration:")
    print(f"   Daily Investment: ${daily_investment:.2f}")
    print()

    # Create CoreStrategy instance
    strategy = CoreStrategy(daily_allocation=daily_investment)

    # Calculate allocations
    equity_pct = strategy.EQUITY_ALLOCATION_PCT
    bond_pct = strategy.BOND_ALLOCATION_PCT
    reit_pct = strategy.REIT_ALLOCATION_PCT
    treasury_pct = strategy.TREASURY_ALLOCATION_PCT

    equity_amount = daily_investment * equity_pct
    bond_amount = daily_investment * bond_pct
    reit_amount = daily_investment * reit_pct
    treasury_amount = daily_investment * treasury_pct

    print("📈 Allocation Breakdown:")
    print(f"   Equity (60%):    ${equity_amount:.2f}")
    print(f"   Bonds (15%):     ${bond_amount:.2f}")
    print(f"   REITs (15%):     ${reit_amount:.2f}")
    print(f"   Treasuries (10%): ${treasury_amount:.2f}")
    print(f"   Total:            ${daily_investment:.2f}")
    print()

    # Check execution threshold
    execution_threshold = 0.50
    print(f"⚙️  Execution Threshold: ${execution_threshold:.2f}")
    print()

    print("✅ Execution Status:")
    print(
        f"   Equity:    {'✅ WILL EXECUTE' if equity_amount >= execution_threshold else '❌ TOO SMALL'}"
    )
    print(
        f"   Bonds:     {'✅ WILL EXECUTE' if bond_amount >= execution_threshold else '❌ TOO SMALL'}"
    )
    print(
        f"   REITs:     {'✅ WILL EXECUTE' if reit_amount >= execution_threshold else '❌ TOO SMALL'}"
    )
    print(
        f"   Treasuries: {'✅ WILL EXECUTE' if treasury_amount >= execution_threshold else '❌ TOO SMALL'}"
    )
    print()

    # Check if VNQ is in ETF universe
    print("📋 ETF Universe:")
    print(f"   Symbols: {', '.join(strategy.DEFAULT_ETF_UNIVERSE)}")
    vnq_in_universe = "VNQ" in strategy.DEFAULT_ETF_UNIVERSE
    vnq_status = "✅ YES" if vnq_in_universe else "❌ NO"
    print(f"   VNQ included: {vnq_status}")
    print()

    # Summary
    print("=" * 80)
    print("SUMMARY:")
    print("=" * 80)

    if reit_amount >= execution_threshold and vnq_in_universe:
        print("✅ REIT trading is CONFIGURED CORRECTLY")
        print(f"   VNQ orders will execute: ${reit_amount:.2f} per day")
        print(f"   This exceeds the ${execution_threshold:.2f} threshold")
    else:
        print("❌ REIT trading has ISSUES:")
        if reit_amount < execution_threshold:
            print(
                f"   - REIT allocation (${reit_amount:.2f}) is below threshold (${execution_threshold:.2f})"
            )
        if not vnq_in_universe:
            print("   - VNQ is not in ETF universe")

    print()
    print("=" * 80)


if __name__ == "__main__":
    test_reit_allocation()
