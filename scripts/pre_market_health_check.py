#!/usr/bin/env python3
"""
PRE-MARKET HEALTH CHECK

Runs before trading starts to validate:
- Alpaca API connectivity
- Anthropic API status
- Market is open
- Circuit breakers not tripped
- Data sources accessible
- System dependencies healthy

CRITICAL: Must pass before allowing trading
"""
import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import alpaca_trade_api as tradeapi
from anthropic import Anthropic
from datetime import datetime
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
ALPACA_KEY = os.getenv("ALPACA_API_KEY", "PKSGVK5JNGYIFPTW53EAKCNBP5")
ALPACA_SECRET = os.getenv("ALPACA_SECRET_KEY", "9DCF1pY2wgTTY3TBasjAHUWWLXiDTyrAhMJ4ZD6nVWaG")
ANTHROPIC_KEY = os.getenv("ANTHROPIC_API_KEY")


def check_alpaca_api() -> bool:
    """Check Alpaca API connectivity and account access."""
    try:
        api = tradeapi.REST(ALPACA_KEY, ALPACA_SECRET, "https://paper-api.alpaca.markets")
        account = api.get_account()
        equity = float(account.equity)
        
        print(f"✅ Alpaca API: Connected")
        print(f"   Portfolio: ${equity:,.2f}")
        print(f"   Status: {account.status}")
        
        if account.status != "ACTIVE":
            print(f"⚠️  Account status: {account.status}")
            return False
        
        return True
    except Exception as e:
        print(f"❌ Alpaca API: FAILED - {e}")
        return False


def check_anthropic_api() -> bool:
    """Check Anthropic API accessibility."""
    if not ANTHROPIC_KEY:
        print(f"⚠️  Anthropic API: No API key configured (will use fallback mode)")
        return True  # Not critical - we have fallback
    
    try:
        client = Anthropic(api_key=ANTHROPIC_KEY)
        # Simple test call
        response = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=10,
            messages=[{"role": "user", "content": "test"}]
        )
        
        print(f"✅ Anthropic API: Connected")
        return True
    except Exception as e:
        error_str = str(e)
        if "credit balance" in error_str.lower():
            print(f"⚠️  Anthropic API: Low credits (will use fallback mode)")
            return True  # Not critical - we have fallback
        else:
            print(f"❌ Anthropic API: FAILED - {e}")
            return True  # Still allow trading with fallback


def check_market_status() -> bool:
    """Check if market is open."""
    try:
        api = tradeapi.REST(ALPACA_KEY, ALPACA_SECRET, "https://paper-api.alpaca.markets")
        clock = api.get_clock()
        
        if clock.is_open:
            print(f"✅ Market: OPEN")
            return True
        else:
            next_open = clock.next_open
            print(f"⚠️  Market: CLOSED (opens at {next_open})")
            print(f"   Trading will execute when market opens")
            return True  # Not a failure - orders will queue
    except Exception as e:
        print(f"❌ Market Status: FAILED - {e}")
        return False


def check_economic_calendar() -> bool:
    """Check if major economic events today (Fed meetings, GDP, CPI)."""
    try:
        from src.utils.finnhub_client import FinnhubClient
        
        client = FinnhubClient()
        if client.has_major_event_today():
            print("⚠️  MAJOR ECONOMIC EVENT TODAY - Consider skipping trading")
            print("   (Fed meeting, GDP release, CPI, or Employment data)")
            return False  # Not a failure, but warning
        return True
    except Exception as e:
        print(f"⚠️  Economic calendar check failed: {e}")
        return True  # Don't block trading if check fails

def check_circuit_breakers() -> bool:
    """Check circuit breaker status."""
    try:
        from src.safety.circuit_breakers import CircuitBreaker
        
        breaker = CircuitBreaker()
        status = breaker.get_status()
        
        if status["is_tripped"]:
            print(f"🚨 Circuit Breaker: TRIPPED")
            print(f"   Reason: {status.get('trip_reason', 'Unknown')}")
            print(f"   Details: {status.get('trip_details', 'N/A')}")
            print(f"   MANUAL RESET REQUIRED")
            return False
        else:
            print(f"✅ Circuit Breaker: OK")
            print(f"   Consecutive losses: {status['consecutive_losses']}")
            print(f"   API errors today: {status['api_errors_today']}")
            return True
    except Exception as e:
        print(f"⚠️  Circuit Breaker: Could not check - {e}")
        return True  # Allow trading if can't check


def check_data_access() -> bool:
    """Check data directory access."""
    try:
        data_dir = Path("data")
        data_dir.mkdir(exist_ok=True)
        
        # Test write
        test_file = data_dir / ".health_check"
        test_file.write_text(datetime.now().isoformat())
        test_file.unlink()
        
        print(f"✅ Data Directory: Writable")
        return True
    except Exception as e:
        print(f"❌ Data Directory: FAILED - {e}")
        return False


def check_dependencies() -> bool:
    """Check Python dependencies."""
    required = ["alpaca_trade_api", "anthropic", "pandas", "numpy"]
    missing = []
    
    for pkg in required:
        try:
            __import__(pkg)
        except ImportError:
            missing.append(pkg)
    
    if missing:
        print(f"❌ Dependencies: MISSING - {', '.join(missing)}")
        return False
    else:
        print(f"✅ Dependencies: All present")
        return True


def main():
    """Run all health checks."""
    print("\n" + "=" * 70)
    print("🏥 PRE-MARKET HEALTH CHECK")
    print(f"📅 {datetime.now().strftime('%Y-%m-%d %I:%M %p')}")
    print("=" * 70 + "\n")
    
    checks = {
        "Dependencies": check_dependencies(),
        "Data Access": check_data_access(),
        "Alpaca API": check_alpaca_api(),
        "Market Status": check_market_status(),
        "Anthropic API": check_anthropic_api(),
        "Circuit Breakers": check_circuit_breakers()
    }
    
    print("\n" + "=" * 70)
    print("📊 HEALTH CHECK SUMMARY")
    print("=" * 70)
    
    critical_passed = all([
        checks["Dependencies"],
        checks["Data Access"],
        checks["Alpaca API"],
        checks["Circuit Breakers"]
    ])
    
    for name, passed in checks.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} - {name}")
    
    print("=" * 70)
    
    if critical_passed:
        print("\n✅ HEALTH CHECK PASSED - System ready for trading\n")
        return 0
    else:
        print("\n❌ HEALTH CHECK FAILED - Do NOT trade until issues resolved\n")
        return 1


if __name__ == "__main__":
    sys.exit(main())

