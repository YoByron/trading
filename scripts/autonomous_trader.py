#!/usr/bin/env python3
"""
AUTONOMOUS DAILY TRADER - FIXED $10/DAY STRATEGY
Runs automatically every day at market open
Uses fixed $10/day investment (not portfolio-based)
Focus: Momentum + Volume confirmation (MACD, RSI, Volume ratio)
"""
import os
import sys
import json
import time as time_module
from datetime import datetime, date, time
from pathlib import Path
import alpaca_trade_api as tradeapi
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from src.utils.data_collector import DataCollector
from src.strategies.core_strategy import CoreStrategy
from src.strategies.growth_strategy import GrowthStrategy
from src.utils.market_data import get_market_data_provider
from src.verification.output_verifier import OutputVerifier  # Claude Agent SDK Loop pattern
from src.orchestration.adk_integration import ADKTradeAdapter  # TURBO MODE: ADK integration

# Configuration
ALPACA_KEY = os.getenv("ALPACA_API_KEY")
ALPACA_SECRET = os.getenv("ALPACA_SECRET_KEY")

# Validate required environment variables
if not ALPACA_KEY or not ALPACA_SECRET:
    raise ValueError(
        "ALPACA_API_KEY and ALPACA_SECRET_KEY must be set in .env file. "
        "Never hardcode API keys in source code."
    )
DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)

# Fixed daily investment (North Star: $10/day Fibonacci strategy)
DAILY_INVESTMENT = float(os.getenv("DAILY_INVESTMENT", "10.0"))

# Position sizing configuration
DEFAULT_RISK_PER_TRADE_PCT = 1.0  # Risk 1% of portfolio per trade
MIN_POSITION_SIZE = 10.0  # Minimum $10 per trade (Alpaca requirement)
MAX_POSITION_SIZE_PCT = 5.0  # Maximum 5% of portfolio per trade
MAX_ORDER_MULTIPLIER = 10.0  # Reject orders >10x expected amount (safety gate)

# Initialize Alpaca
api = tradeapi.REST(ALPACA_KEY, ALPACA_SECRET, "https://paper-api.alpaca.markets")
market_data_provider = get_market_data_provider()

# TURBO MODE: Initialize ADK adapter (enabled by default, can disable via ADK_ENABLED=0)
adk_enabled = os.getenv("ADK_ENABLED", "1").lower() not in {"0", "false", "off", "no"}
adk_adapter = ADKTradeAdapter(
    enabled=adk_enabled,
    base_url=os.getenv("ADK_BASE_URL", "http://127.0.0.1:8080/api"),
    app_name=os.getenv("ADK_APP_NAME", "trading_orchestrator"),
    root_agent_name=os.getenv("ADK_ROOT_AGENT", "trading_orchestrator_root_agent"),
    user_id=os.getenv("ADK_USER_ID", "autonomous_trader"),
)
if adk_adapter.enabled:
    print("🚀 TURBO MODE: ADK orchestrator ENABLED")
else:
    print("⚠️  ADK orchestrator disabled (set ADK_ENABLED=1 to enable)")


def calculate_daily_investment():
    """
    Calculate daily investment amount - FIXED $10/day strategy.

    Uses DAILY_INVESTMENT from environment or defaults to $10.00.
    This matches the North Star goal of Fibonacci compounding starting at $10/day.

    Returns:
        Daily total investment amount in dollars (fixed, not portfolio-based)
    """
    return DAILY_INVESTMENT


def validate_order_size(amount: float, expected: float, tier: str) -> tuple[bool, str]:
    """
    Validate order size before execution.
    
    Rejects orders that exceed MAX_ORDER_MULTIPLIER times expected amount.
    This prevents catastrophic errors like the Nov 3 $1,600 order (200x expected).
    
    Args:
        amount: Proposed order amount
        expected: Expected order amount for this tier
        tier: Tier name for logging
    
    Returns:
        (is_valid, error_message)
    """
    if amount > expected * MAX_ORDER_MULTIPLIER:
        error_msg = (
            f"🚨 ORDER REJECTED: ${amount:.2f} exceeds ${expected * MAX_ORDER_MULTIPLIER:.2f} "
            f"({MAX_ORDER_MULTIPLIER}x expected ${expected:.2f} for {tier})"
        )
        print(f"❌ {error_msg}")
        return False, error_msg
    
    if amount < MIN_POSITION_SIZE:
        error_msg = f"⚠️  Order ${amount:.2f} below minimum ${MIN_POSITION_SIZE:.2f}"
        print(f"❌ {error_msg}")
        return False, error_msg
    
    return True, ""


def log_trade(trade_data):
    """Log trade to daily record"""
    log_file = DATA_DIR / f"trades_{date.today().isoformat()}.json"

    trades = []
    if log_file.exists():
        with open(log_file, "r") as f:
            trades = json.load(f)

    trades.append(trade_data)

    with open(log_file, "w") as f:
        json.dump(trades, f, indent=2)


def wait_for_market_stabilization():
    """Wait 5-10 minutes after market open for price stabilization"""
    now = datetime.now().time()
    market_open = time(9, 30)
    stabilization_time = time(9, 40)  # Wait until 9:40 AM

    if market_open <= now < stabilization_time:
        wait_until = datetime.combine(date.today(), stabilization_time)
        wait_seconds = (wait_until - datetime.now()).total_seconds()

        if wait_seconds > 0:
            print(f"⏰ Market just opened. Waiting {wait_seconds/60:.1f} minutes for stabilization...")
            time_module.sleep(wait_seconds)
            print("✅ Stabilization period complete. Proceeding with analysis...")


def validate_data_freshness(symbol, hist_data):
    """Ensure market data is fresh (< 2 hours old) to prevent stale data trades"""
    if hist_data is None or hist_data.empty:
        print(f"⚠️  {symbol}: No data available")
        return False

    try:
        latest_timestamp = hist_data.index[-1]
        age_hours = (datetime.now() - latest_timestamp).total_seconds() / 3600

        if age_hours > 2:
            print(f"⚠️  {symbol}: Data is {age_hours:.1f}h old - TOO STALE (rejecting)")
            return False

        print(f"✅ {symbol}: Data is {age_hours:.1f}h old - FRESH")
        return True
    except Exception as e:
        print(f"⚠️  {symbol}: Error checking data freshness: {e}")
        return False


def calculate_technical_score(symbol):
    """Calculate technical score with MACD, RSI, volume (matching backtest logic)"""
    try:
        try:
            result = market_data_provider.get_daily_bars(symbol, lookback_days=60)
            hist = result.data  # Extract DataFrame from MarketDataResult
        except ValueError as exc:
            print(f"❌ {symbol}: Market data unavailable: {exc}")
            return 0

        if hist.empty or len(hist) < 26:
            print(
                f"⚠️  {symbol}: Insufficient data ({len(hist) if not hist.empty else 0} days)"
            )
            return 0

        # Validate data freshness
        if not validate_data_freshness(symbol, hist):
            return 0  # Reject stale data

        # Calculate MACD
        ema12 = hist['Close'].ewm(span=12, adjust=False).mean()
        ema26 = hist['Close'].ewm(span=26, adjust=False).mean()
        macd_line = ema12 - ema26
        signal_line = macd_line.ewm(span=9, adjust=False).mean()
        histogram = macd_line - signal_line

        # Calculate RSI
        delta = hist['Close'].diff()
        gain = delta.where(delta > 0, 0).rolling(window=14).mean()
        loss = -delta.where(delta < 0, 0).rolling(window=14).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))

        # Calculate volume ratio
        avg_volume = hist['Volume'].rolling(window=20).mean()
        volume_ratio = hist['Volume'].iloc[-1] / avg_volume.iloc[-1]

        # Get current values
        macd_hist = histogram.iloc[-1]
        rsi_val = rsi.iloc[-1]
        price = hist['Close'].iloc[-1]

        # CRITICAL FILTERS (matching backtest)
        if macd_hist < 0:
            print(f"❌ {symbol}: REJECTED - Bearish MACD histogram ({macd_hist:.3f})")
            return 0

        if rsi_val > 70:
            print(f"❌ {symbol}: REJECTED - Overbought RSI ({rsi_val:.1f})")
            return 0

        if volume_ratio < 0.8:
            print(f"❌ {symbol}: REJECTED - Low volume ({volume_ratio:.2f}x)")
            return 0

        # Calculate composite score (price weighted by technical strength)
        technical_score = price * (1 + macd_hist/10) * (1 + (70-rsi_val)/100) * volume_ratio

        print(f"✅ {symbol}: Score {technical_score:.2f} | MACD: {macd_hist:.3f} | RSI: {rsi_val:.1f} | Vol: {volume_ratio:.2f}x")
        return technical_score

    except Exception as e:
        print(f"❌ {symbol}: Error calculating technical score: {e}")
        return 0


def execute_tier1(daily_amount):
    """Tier 1: Core ETF Strategy - 70% using PROPER technical analysis"""
    amount = daily_amount * 0.70

    print("\n" + "=" * 70)
    print("🎯 TIER 1: CORE ETF STRATEGY (MACD + RSI + Volume)")
    print("=" * 70)

    etfs = ["SPY", "QQQ", "VOO"]
    scores = {}

    # Analyze each ETF with REAL technical indicators
    for symbol in etfs:
        score = calculate_technical_score(symbol)
        scores[symbol] = score

    # Filter out zeros (rejected symbols)
    valid_scores = {k: v for k, v in scores.items() if v > 0}

    if not valid_scores:
        print("\n❌ NO VALID ENTRIES - All symbols rejected by technical filters")
        print("💡 Skipping Tier 1 trade today (safety first)")
        return False

    # Select best
    best = max(valid_scores, key=valid_scores.get)

    print(f"\n✅ Selected: {best}")
    print(f"💰 Investment: ${amount:.2f} (70% of ${daily_amount:.2f})")

    # VALIDATION GATE: Check order size before execution
    is_valid, error_msg = validate_order_size(amount, daily_amount * 0.70, "T1_CORE")
    if not is_valid:
        print(f"❌ Tier 1 trade rejected: {error_msg}")
        return False

    try:
        # Place order
        order = api.submit_order(
            symbol=best, notional=amount, side="buy", type="market", time_in_force="day"
        )

        print(f"✅ Order placed: {order.id}")

        # Log trade
        log_trade(
            {
                "timestamp": datetime.now().isoformat(),
                "tier": "T1_CORE",
                "symbol": best,
                "amount": amount,
                "order_id": order.id,
                "status": order.status,
            }
        )

        return True
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def execute_tier2(daily_amount):
    """Tier 2: Disruptive Innovation Strategy - 30% using PROPER technical analysis

    Focus: NVDA (AI infrastructure) + GOOGL (Autonomous vehicles) + AMZN (OpenAI deal)
    Conservative approach - proven disruptive leaders
    """
    amount = daily_amount * 0.30

    print("\n" + "=" * 70)
    print("📈 TIER 2: DISRUPTIVE INNOVATION STRATEGY (MACD + RSI + Volume)")
    print("=" * 70)

    # Focus on NVDA + GOOGL + AMZN (3-way rotation based on REAL momentum)
    stocks = ["NVDA", "GOOGL", "AMZN"]
    scores = {}

    # Analyze REAL technical indicators for each
    for symbol in stocks:
        score = calculate_technical_score(symbol)
        scores[symbol] = score

    # Filter out zeros (rejected symbols)
    valid_scores = {k: v for k, v in scores.items() if v > 0}

    if not valid_scores:
        print("\n❌ NO VALID ENTRIES - All symbols rejected by technical filters")
        print("💡 Skipping Tier 2 trade today (safety first)")
        return False

    # Select best technical score
    selected = max(valid_scores, key=valid_scores.get)

    print(f"\n✅ Selected: {selected}")
    print(f"💰 Investment: ${amount:.2f} (30% of ${daily_amount:.2f})")

    # Display disruptive theme
    themes = {
        'NVDA': 'AI Infrastructure',
        'GOOGL': 'Autonomous Vehicles + AI',
        'AMZN': 'OpenAI $38B Deal + Cloud AI'
    }
    print(f"🎯 Disruptive Theme: {themes.get(selected, 'Innovation')}")

    # VALIDATION GATE: Check order size before execution
    is_valid, error_msg = validate_order_size(amount, daily_amount * 0.30, "T2_GROWTH")
    if not is_valid:
        print(f"❌ Tier 2 trade rejected: {error_msg}")
        return False

    try:
        order = api.submit_order(
            symbol=selected,
            notional=amount,
            side="buy",
            type="market",
            time_in_force="day",
        )

        print(f"✅ Order placed: {order.id}")

        log_trade(
            {
                "timestamp": datetime.now().isoformat(),
                "tier": "T2_GROWTH",
                "symbol": selected,
                "amount": amount,
                "order_id": order.id,
                "status": order.status,
            }
        )

        return True
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def track_daily_deposit(daily_amount):
    """Track 10% each for Tier 3 (IPO) and Tier 4 (Crowdfunding)"""
    ipo_amount = daily_amount * 0.10
    crowdfunding_amount = daily_amount * 0.10

    print("\n" + "=" * 70)
    print("💰 TIER 3 & 4: MANUAL INVESTMENT TRACKING")
    print("=" * 70)

    tracking_file = DATA_DIR / "manual_investments.json"

    data = {"ipo_reserve": 0, "crowdfunding_reserve": 0, "history": []}
    if tracking_file.exists():
        with open(tracking_file, "r") as f:
            data = json.load(f)

    # Add daily allocation to reserves
    data["ipo_reserve"] += ipo_amount
    data["crowdfunding_reserve"] += crowdfunding_amount
    data["history"].append(
        {
            "date": date.today().isoformat(),
            "ipo_deposit": ipo_amount,
            "crowdfunding_deposit": crowdfunding_amount,
        }
    )

    with open(tracking_file, "w") as f:
        json.dump(data, f, indent=2)

    print(f"✅ IPO Reserve: ${data['ipo_reserve']:.2f} (+${ipo_amount:.2f} today)")
    print(f"✅ Crowdfunding Reserve: ${data['crowdfunding_reserve']:.2f} (+${crowdfunding_amount:.2f} today)")
    print("💡 Manual investments ready when opportunities arise")


def get_account_summary():
    """Get current account performance"""
    account = api.get_account()

    return {
        "equity": float(account.equity),
        "cash": float(account.cash),
        "buying_power": float(account.buying_power),
        "pl": float(account.equity) - 100000.0,  # Starting balance
        "pl_pct": ((float(account.equity) - 100000.0) / 100000.0) * 100,
    }


def update_performance_log():
    """Update daily performance log"""
    perf_file = DATA_DIR / "performance_log.json"

    perf_data = []
    if perf_file.exists():
        with open(perf_file, "r") as f:
            perf_data = json.load(f)

    summary = get_account_summary()
    summary["date"] = date.today().isoformat()
    summary["timestamp"] = datetime.now().isoformat()

    perf_data.append(summary)

    with open(perf_file, "w") as f:
        json.dump(perf_data, f, indent=2)

    return summary


def main():
    """Main autonomous trading execution with intelligent position sizing"""
    print("\n" + "=" * 70)
    print("🤖 AUTONOMOUS DAILY TRADER - WORLD-CLASS AI SYSTEM")
    print(f"📅 Date: {datetime.now().strftime('%Y-%m-%d %I:%M %p')}")
    print("=" * 70)

    # Calculate current trading day
    challenge_file = DATA_DIR / "challenge_start.json"

    if not challenge_file.exists():
        # First day!
        start_data = {
            "start_date": date.today().isoformat(),
            "starting_balance": 100000.0,
        }
        with open(challenge_file, "w") as f:
            json.dump(start_data, f, indent=2)
        current_day = 1
    else:
        with open(challenge_file, "r") as f:
            data = json.load(f)
        start_date = datetime.fromisoformat(data["start_date"]).date()
        today = date.today()
        current_day = (today - start_date).days + 1

    # Get current account value (for reporting only)
    account = api.get_account()
    account_value = float(account.equity)

    # Fixed $10/day investment (North Star Fibonacci strategy)
    daily_investment = calculate_daily_investment()

    print(f"📊 Trading Day: {current_day}")
    print(f"💰 Portfolio Value: ${account_value:,.2f}")
    print(f"📈 Daily Investment: ${daily_investment:.2f} (FIXED - not portfolio-based)")
    print("🎯 Strategy: Momentum (MACD + RSI + Volume)")
    print(f"📊 Breakdown: Core 70% (${daily_investment*0.7:.2f}) | Growth 30% (${daily_investment*0.3:.2f})")
    print("=" * 70)

    # Check if market is open
    clock = api.get_clock()
    if not clock.is_open:
        print("⚠️  Market is closed. Order will execute at next open.")
    else:
        # Wait for market stabilization (5-10 min post-open)
        wait_for_market_stabilization()

    # TURBO MODE: Try ADK orchestrator first (if enabled)
    adk_used = False
    tier1_success = False
    tier2_success = False
    
    if adk_adapter.enabled:
        try:
            print("\n" + "=" * 70)
            print("🚀 TURBO MODE: Attempting ADK orchestrator evaluation")
            print("=" * 70)
            
            context = {
                "mode": "paper",
                "daily_investment": daily_investment,
                "tier1_allocation": daily_investment * 0.70,
                "tier2_allocation": daily_investment * 0.30,
                "account_value": account_value,
            }
            
            # Try ADK for Tier 1 (Core ETF)
            tier1_symbols = ["SPY", "QQQ", "VOO"]
            tier1_decision = adk_adapter.evaluate(
                symbols=tier1_symbols,
                context={**context, "tier": "T1_CORE"},
            )
            
            if tier1_decision and tier1_decision.action == "BUY":
                print(f"✅ ADK Tier 1 Decision: {tier1_decision.symbol} BUY (confidence: {tier1_decision.confidence:.2f})")
                amount = tier1_decision.position_size or (daily_investment * 0.70)
                is_valid, error_msg = validate_order_size(amount, daily_investment * 0.70, "T1_CORE_ADK")
                if is_valid:
                    try:
                        order = api.submit_order(
                            symbol=tier1_decision.symbol,
                            notional=amount,
                            side="buy",
                            type="market",
                            time_in_force="day"
                        )
                        print(f"✅ ADK Tier 1 Order placed: {order.id}")
                        log_trade({
                            "timestamp": datetime.now().isoformat(),
                            "tier": "T1_CORE_ADK",
                            "symbol": tier1_decision.symbol,
                            "amount": amount,
                            "order_id": order.id,
                            "status": order.status,
                            "adk_confidence": tier1_decision.confidence,
                        })
                        tier1_success = True
                        adk_used = True
                    except Exception as e:
                        print(f"❌ ADK Tier 1 order failed: {e}")
                        tier1_success = False
                else:
                    print(f"❌ ADK Tier 1 order rejected: {error_msg}")
                    tier1_success = False
            else:
                print("⚠️  ADK Tier 1: No BUY decision (will fallback to rule-based)")
                tier1_success = False
            
            # Try ADK for Tier 2 (Growth)
            tier2_symbols = ["NVDA", "GOOGL", "AMZN"]
            tier2_decision = adk_adapter.evaluate(
                symbols=tier2_symbols,
                context={**context, "tier": "T2_GROWTH"},
            )
            
            if tier2_decision and tier2_decision.action == "BUY":
                print(f"✅ ADK Tier 2 Decision: {tier2_decision.symbol} BUY (confidence: {tier2_decision.confidence:.2f})")
                amount = tier2_decision.position_size or (daily_investment * 0.30)
                is_valid, error_msg = validate_order_size(amount, daily_investment * 0.30, "T2_GROWTH_ADK")
                if is_valid:
                    try:
                        order = api.submit_order(
                            symbol=tier2_decision.symbol,
                            notional=amount,
                            side="buy",
                            type="market",
                            time_in_force="day"
                        )
                        print(f"✅ ADK Tier 2 Order placed: {order.id}")
                        log_trade({
                            "timestamp": datetime.now().isoformat(),
                            "tier": "T2_GROWTH_ADK",
                            "symbol": tier2_decision.symbol,
                            "amount": amount,
                            "order_id": order.id,
                            "status": order.status,
                            "adk_confidence": tier2_decision.confidence,
                        })
                        tier2_success = True
                        adk_used = True
                    except Exception as e:
                        print(f"❌ ADK Tier 2 order failed: {e}")
                        tier2_success = False
                else:
                    print(f"❌ ADK Tier 2 order rejected: {error_msg}")
                    tier2_success = False
            else:
                print("⚠️  ADK Tier 2: No BUY decision (will fallback to rule-based)")
                tier2_success = False
                
        except Exception as e:
            print(f"⚠️  ADK orchestrator error: {e}")
            print("   Falling back to rule-based strategies")
            import traceback
            traceback.print_exc()
            tier1_success = False
            tier2_success = False
    
    # Fallback to rule-based strategies if ADK not used or failed
    if not adk_used:
        print("\n" + "=" * 70)
        print("📊 Using rule-based strategies (MACD + RSI + Volume)")
        print("=" * 70)
        # Execute strategies with PROPER technical analysis
        tier1_success = execute_tier1(daily_investment)
        tier2_success = execute_tier2(daily_investment)
    
    track_daily_deposit(daily_investment)

    # Update performance
    print("\n" + "=" * 70)
    print("📊 PERFORMANCE UPDATE")
    print("=" * 70)

    perf = update_performance_log()
    print(f"💰 Equity: ${perf['equity']:,.2f}")
    print(f"📈 P/L: ${perf['pl']:+,.2f} ({perf['pl_pct']:+.2f}%)")
    print(f"💵 Cash: ${perf['cash']:,.2f}")

    # Collect historical data for ML training
    print("\n📊 Collecting historical data for ML training...")
    try:
        collector = DataCollector(data_dir="data/historical")
        symbols = ["SPY", "QQQ", "VOO", "NVDA", "GOOGL", "AMZN"]
        collector.collect_daily_data(symbols, lookback_days=30)
        print("✅ Historical data collection complete")
    except Exception as e:
        print(f"⚠️  Data collection failed: {str(e)}")

    # VERIFY OUTPUT (Claude Agent SDK Loop Pattern)
    print("\n" + "=" * 70)
    print("🔍 OUTPUT VERIFICATION (Claude Agent SDK Loop)")
    print("=" * 70)
    try:
        verifier = OutputVerifier()
        success, results = verifier.verify_system_state()

        if success:
            print("✅ VERIFICATION PASSED - All critical rules satisfied")
        else:
            print("❌ VERIFICATION FAILED - Critical issues detected:")
            for issue in results["critical"]:
                print(f"  🚨 {issue}")

        if results["warning"]:
            print("\n⚠️  WARNINGS:")
            for warning in results["warning"]:
                print(f"  ⚠️  {warning}")

        # Verify portfolio claims (anti-lying check)
        accurate, message = verifier.verify_portfolio_claims(
            claimed_pl=perf['pl'],
            claimed_equity=perf['equity']
        )
        if not accurate:
            print(f"\n🚨 ANTI-LYING VIOLATION: {message}")
        else:
            print(f"✅ Portfolio claims verified accurate")

    except Exception as e:
        print(f"⚠️  Verification failed: {str(e)}")

    # Summary
    print("\n" + "=" * 70)
    print("✅ DAILY EXECUTION COMPLETE")
    print("=" * 70)
    print(f"Tier 1 (Core): {'✅' if tier1_success else '❌'}")
    print(f"Tier 2 (Growth): {'✅' if tier2_success else '❌'}")
    print("Tier 3 (IPO): ✅ Tracked")
    print("Tier 4 (Crowdfunding): ✅ Tracked")
    print(f"\n📁 Logs saved to: {DATA_DIR}")
    print("🎯 Next execution: Tomorrow 9:35 AM ET")
    print("=" * 70)


if __name__ == "__main__":
    main()
