#!/usr/bin/env python3
"""
Test script for order amount validation.

This script tests the new validation logic that prevents catastrophic
order size errors like the Nov 3 incident ($1,600 instead of $8).

Tests:
1. Normal orders ($6 for T1_CORE) - should PASS
2. Large but acceptable orders ($60 = 10x) - should PASS with warning
3. Catastrophic orders ($600 = 100x) - should ERROR and reject
4. 200x order like Nov 3 ($1,200) - should ERROR and reject
"""

import os
import sys
import logging

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

# Set environment for testing
os.environ["DAILY_INVESTMENT"] = "10.0"
os.environ["ALPACA_API_KEY"] = "test_key"
os.environ["ALPACA_SECRET_KEY"] = "test_secret"

from src.core.alpaca_trader import AlpacaTrader, OrderExecutionError

# Configure logging to see validation messages
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

def run_tests():
    """Run validation tests."""
    print("=" * 80)
    print("ORDER VALIDATION TEST SUITE")
    print("=" * 80)
    print()

    # Get daily investment from environment
    daily_investment = float(os.getenv("DAILY_INVESTMENT", "10.0"))
    print(f"Daily Investment: ${daily_investment}")
    print(f"T1_CORE Expected: ${daily_investment * 0.60} (60% allocation)")
    print(f"T2_GROWTH Expected: ${daily_investment * 0.20} (20% allocation)")
    print()

    # Initialize trader (won't connect to Alpaca for validation tests)
    try:
        trader = AlpacaTrader(paper=True)
        print(f"✅ AlpacaTrader initialized with daily_investment=${trader.daily_investment}")
        print()
    except Exception as e:
        print(f"⚠️  Could not connect to Alpaca (expected if no credentials): {e}")
        print("Continuing with validation tests using mock trader...")
        print()
        # Create mock trader for validation testing
        class MockTrader:
            def __init__(self):
                self.daily_investment = float(os.getenv("DAILY_INVESTMENT", "10.0"))
                self.TIER_ALLOCATIONS = AlpacaTrader.TIER_ALLOCATIONS
                self.MAX_ORDER_MULTIPLIER = AlpacaTrader.MAX_ORDER_MULTIPLIER

            validate_order_amount = AlpacaTrader.validate_order_amount

        trader = MockTrader()

    # Test cases
    test_cases = [
        {
            "name": "Normal T1_CORE order ($6)",
            "symbol": "SPY",
            "amount": 6.0,
            "tier": "T1_CORE",
            "should_pass": True,
            "description": "Expected daily T1 core allocation"
        },
        {
            "name": "Normal T2_GROWTH order ($2)",
            "symbol": "NVDA",
            "amount": 2.0,
            "tier": "T2_GROWTH",
            "should_pass": True,
            "description": "Expected daily T2 growth allocation"
        },
        {
            "name": "5x order ($30)",
            "symbol": "SPY",
            "amount": 30.0,
            "tier": "T1_CORE",
            "should_pass": True,
            "description": "5x expected - WARNING but allowed"
        },
        {
            "name": "10x order ($60)",
            "symbol": "SPY",
            "amount": 60.0,
            "tier": "T1_CORE",
            "should_pass": True,
            "description": "10x expected - WARNING but at limit"
        },
        {
            "name": "15x order ($90)",
            "symbol": "SPY",
            "amount": 90.0,
            "tier": "T1_CORE",
            "should_pass": False,
            "description": "15x expected - SHOULD BE REJECTED"
        },
        {
            "name": "100x order ($600)",
            "symbol": "SPY",
            "amount": 600.0,
            "tier": "T1_CORE",
            "should_pass": False,
            "description": "100x expected - SHOULD BE REJECTED"
        },
        {
            "name": "200x order like Nov 3 ($1,200)",
            "symbol": "SPY",
            "amount": 1200.0,
            "tier": "T1_CORE",
            "should_pass": False,
            "description": "200x expected - THIS IS WHAT HAPPENED NOV 3"
        },
    ]

    # Run tests
    passed = 0
    failed = 0

    for i, test in enumerate(test_cases, 1):
        print(f"TEST {i}: {test['name']}")
        print(f"  Description: {test['description']}")
        print(f"  Symbol: {test['symbol']}, Amount: ${test['amount']}, Tier: {test['tier']}")

        try:
            trader.validate_order_amount(test['symbol'], test['amount'], test['tier'])

            if test['should_pass']:
                print(f"  ✅ PASS - Order accepted as expected")
                passed += 1
            else:
                print(f"  ❌ FAIL - Order should have been REJECTED but was ACCEPTED")
                failed += 1

        except OrderExecutionError as e:
            if not test['should_pass']:
                print(f"  ✅ PASS - Order rejected as expected")
                print(f"  Error message preview: {str(e)[:100]}...")
                passed += 1
            else:
                print(f"  ❌ FAIL - Order should have been ACCEPTED but was REJECTED")
                print(f"  Error: {e}")
                failed += 1

        except Exception as e:
            print(f"  ❌ FAIL - Unexpected error: {e}")
            failed += 1

        print()

    # Summary
    print("=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    print(f"Total Tests: {len(test_cases)}")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    print()

    if failed == 0:
        print("🎉 ALL TESTS PASSED! 🎉")
        print("The Nov 3 incident would have been PREVENTED by this validation.")
        return True
    else:
        print(f"⚠️  {failed} TESTS FAILED")
        return False

if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
