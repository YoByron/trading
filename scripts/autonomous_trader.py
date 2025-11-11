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
ALPACA_DATA_FEED = os.getenv("ALPACA_DATA_FEED", "iex").lower()

# Position sizing configuration
DEFAULT_RISK_PER_TRADE_PCT = 1.0  # Risk 1% of portfolio per trade
MIN_POSITION_SIZE = 10.0  # Minimum $10 per trade (Alpaca requirement)
MAX_POSITION_SIZE_PCT = 5.0  # Maximum 5% of portfolio per trade

# Initialize Alpaca
api = tradeapi.REST(ALPACA_KEY, ALPACA_SECRET, "https://paper-api.alpaca.markets")


def calculate_daily_investment():
    """
    Calculate daily investment amount - FIXED $10/day strategy.

    Uses DAILY_INVESTMENT from environment or defaults to $10.00.
    This matches the North Star goal of Fibonacci compounding starting at $10/day.

    Returns:
        Daily total investment amount in dollars (fixed, not portfolio-based)
    """
    return DAILY_INVESTMENT


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
        # Try yfinance first
        import yfinance as yf
        import pandas as pd

        ticker = yf.Ticker(symbol)
        # Use explicit dates instead of period to avoid timezone lookup rate limiting
        from datetime import timedelta
        end_date = datetime.now()
        start_date = end_date - timedelta(days=60)  # 60 calendar days = ~50 trading days
        hist = ticker.history(start=start_date, end=end_date)

        # If yfinance fails, use Alpaca as fallback
        if hist.empty or len(hist) < 26:
            print(f"⚠️  {symbol}: yfinance failed, trying Alpaca fallback...")
            try:
                # Get 100 days from Alpaca (need 50+ trading days for MACD)
                from datetime import timedelta
                end_date = datetime.now()
                start_date = end_date - timedelta(days=100)

                bars = api.get_bars(
                    symbol,
                    "1Day",
                    start=start_date.strftime("%Y-%m-%d"),
                    end=end_date.strftime("%Y-%m-%d"),
                    feed=ALPACA_DATA_FEED
                ).df
                if not bars.empty:
                    # Convert Alpaca format to yfinance format
                    hist = pd.DataFrame({
                        'Close': bars['close'],
                        'Volume': bars['volume'],
                        'Open': bars['open'],
                        'High': bars['high'],
                        'Low': bars['low']
                    })
                    print(f"✅ {symbol}: Using Alpaca data ({len(hist)} days)")
                else:
                    print(f"❌ {symbol}: Alpaca also failed - no data available")
                    return 0
            except Exception as e:
                print(f"❌ {symbol}: Both yfinance and Alpaca failed: {e}")
                return 0

        if hist.empty or len(hist) < 26:
            print(f"⚠️  {symbol}: Insufficient data ({len(hist) if not hist.empty else 0} days)")
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
    """Tier 1: Core ETF Strategy - 60% using PROPER technical analysis"""
    amount = daily_amount * 0.60

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
    print(f"💰 Investment: ${amount:.2f} (60% of ${daily_amount:.2f})")

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
    """Tier 2: Disruptive Innovation Strategy - 20% using PROPER technical analysis

    Focus: NVDA (AI infrastructure) + GOOGL (Autonomous vehicles) + AMZN (OpenAI deal)
    Conservative approach - proven disruptive leaders
    """
    amount = daily_amount * 0.20

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
    print(f"💰 Investment: ${amount:.2f} (20% of ${daily_amount:.2f})")

    # Display disruptive theme
    themes = {
        'NVDA': 'AI Infrastructure',
        'GOOGL': 'Autonomous Vehicles + AI',
        'AMZN': 'OpenAI $38B Deal + Cloud AI'
    }
    print(f"🎯 Disruptive Theme: {themes.get(selected, 'Innovation')}")

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
    print(f"📊 Breakdown: Core 60% (${daily_investment*0.6:.2f}) | Growth 20% (${daily_investment*0.2:.2f}) | IPO 10% (${daily_investment*0.1:.2f}) | Crowdfunding 10% (${daily_investment*0.1:.2f})")
    print("=" * 70)

    # Check if market is open
    clock = api.get_clock()
    if not clock.is_open:
        print("⚠️  Market is closed. Order will execute at next open.")
    else:
        # Wait for market stabilization (5-10 min post-open)
        wait_for_market_stabilization()

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
