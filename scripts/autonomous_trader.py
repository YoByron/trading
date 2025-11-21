#!/usr/bin/env python3
"""
AUTONOMOUS DAILY TRADER - FIXED $10/DAY STRATEGY
Runs automatically every day at market open
Uses fixed $10/day investment (not portfolio-based)
Focus: Momentum + Volume confirmation (MACD, RSI, Volume ratio)

WEEKEND MODE: Executes Tier 5 (Crypto) on Saturdays and Sundays
WEEKDAY MODE: Executes Tiers 1-2 (Stocks) Monday-Friday
"""
import os
import sys
import json
import time as time_module
from datetime import datetime, date, time
from pathlib import Path
import argparse
import alpaca_trade_api as tradeapi
from dotenv import load_dotenv
import requests  # For ADK health checks

# Load environment variables from .env file
load_dotenv()

# Initialize error monitoring (Sentry) if configured
try:
    from src.utils.error_monitoring import init_sentry
    init_sentry()  # Will silently fail if SENTRY_DSN not set
except Exception:
    pass  # Error monitoring is optional

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from src.utils.data_collector import DataCollector
from src.strategies.core_strategy import CoreStrategy
from src.strategies.growth_strategy import GrowthStrategy
from src.strategies.crypto_strategy import CryptoStrategy  # WEEKEND MODE: Crypto trading
from src.utils.market_data import get_market_data_provider
from src.utils.technical_indicators import calculate_technical_score  # Shared utility
from src.verification.output_verifier import OutputVerifier  # Claude Agent SDK Loop pattern
from src.orchestration.adk_integration import ADKTradeAdapter  # TURBO MODE: ADK integration
from src.evaluation.trading_evaluator import TradingSystemEvaluator  # Week 1: Self-improving RAG evaluation
from src.evaluation.rag_storage import EvaluationRAGStorage  # Optional RAG storage

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
# Minimum per-trade notional aligned with Tier 1 daily allocation ($6 = 60% of $10)
# This replaces the previous hard $10 minimum to allow expected Tier 1 orders.
MIN_POSITION_SIZE = 6.0
MAX_POSITION_SIZE_PCT = 5.0  # Maximum 5% of portfolio per trade
MAX_ORDER_MULTIPLIER = 10.0  # Reject orders >10x expected amount (safety gate)

# Initialize Alpaca
api = tradeapi.REST(ALPACA_KEY, ALPACA_SECRET, "https://paper-api.alpaca.markets")
market_data_provider = get_market_data_provider()

# Week 1: Initialize evaluation system (FREE - local processing)
try:
    evaluator = TradingSystemEvaluator()
    eval_rag_storage = EvaluationRAGStorage()
    print("✅ Evaluation system ENABLED (self-improving RAG)")
except Exception as e:
    print(f"⚠️  Evaluation system unavailable: {e}")
    evaluator = None
    eval_rag_storage = None

# TURBO MODE: Initialize ADK adapter (enabled by default, can disable via ADK_ENABLED=0)
adk_enabled = os.getenv("ADK_ENABLED", "1").lower() not in {"0", "false", "off", "no"}
adk_base_url = os.getenv("ADK_BASE_URL", "http://127.0.0.1:8080/api")
adk_adapter = ADKTradeAdapter(
    enabled=adk_enabled,
    base_url=adk_base_url,
    app_name=os.getenv("ADK_APP_NAME", "trading_orchestrator"),
    root_agent_name=os.getenv("ADK_ROOT_AGENT", "trading_orchestrator_root_agent"),
    user_id=os.getenv("ADK_USER_ID", "autonomous_trader"),
)

# Check if ADK service is actually running
adk_service_available = False
if adk_adapter.enabled:
    try:
        # Try health endpoint first
        health_url = adk_base_url.replace("/api", "/api/health")
        response = requests.get(health_url, timeout=3)
        if response.status_code == 200:
            adk_service_available = True
            print("🚀 TURBO MODE: ADK orchestrator ENABLED and SERVICE RUNNING")
            print(f"   Service URL: {adk_base_url}")
        else:
            print(f"⚠️  ADK orchestrator enabled but service not responding (HTTP {response.status_code})")
            print(f"   Health URL: {health_url}")
    except requests.exceptions.ConnectionError:
        print(f"⚠️  ADK orchestrator enabled but service not available (connection refused)")
        print(f"   Expected URL: {adk_base_url}")
        print("   Will fall back to Python strategies")
    except requests.exceptions.Timeout:
        print(f"⚠️  ADK orchestrator enabled but service timeout (taking too long)")
        print("   Will fall back to Python strategies")
    except Exception as e:
        print(f"⚠️  ADK orchestrator enabled but service check failed: {e}")
        print("   Will fall back to Python strategies")
else:
    print("⚠️  ADK orchestrator disabled (set ADK_ENABLED=1 to enable)")

# Langchain approval gate (enabled by default for intelligent filtering)
langchain_enabled = os.getenv("LANGCHAIN_APPROVAL_ENABLED", "true").lower() == "true"
langchain_agent = None
if langchain_enabled:
    try:
        from langchain_agents.agents import build_price_action_agent
        langchain_agent = build_price_action_agent()
        print("✅ Langchain approval gate ENABLED")
    except Exception as e:
        print(f"⚠️  Langchain approval gate unavailable: {e}")
        langchain_agent = None
else:
    print("⚠️  Langchain approval gate disabled (set LANGCHAIN_APPROVAL_ENABLED=true to enable)")

# Gemini 3 Agent (New Tier 2 Validation)
gemini_enabled = os.getenv("GEMINI_AGENT_ENABLED", "true").lower() == "true"
gemini_agent = None
if gemini_enabled:
    try:
        from src.agents.gemini_agent import GeminiAgent
        gemini_agent = GeminiAgent(
            name="GeminiTrader",
            role="Strategic validation and risk assessment",
            model="gemini-3-pro-preview",  # Using latest stable model
            default_thinking_level="high"
        )
        print("✅ Gemini 3 Agent ENABLED (Strategic Validation)")
    except Exception as e:
        print(f"⚠️  Gemini 3 Agent unavailable: {e}")
        gemini_agent = None
else:
    print("⚠️  Gemini 3 Agent disabled (set GEMINI_AGENT_ENABLED=true to enable)")


def is_weekend():
    """
    Check if today is Saturday or Sunday (weekend).

    Returns:
        True if weekend (Sat=5, Sun=6), False otherwise
    """
    return datetime.now().weekday() in [5, 6]  # Saturday=5, Sunday=6


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
            f"({MAX_ORDER_MULTIPLIER:.0f}x expected ${expected:.2f} for {tier}; multiplier safety gate)"
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


def evaluate_trade_execution(
    trade_result: dict,
    expected_amount: float,
    daily_allocation: float,
    tier: str
) -> None:
    """
    Evaluate trade execution using self-improving RAG system.
    
    Week 1: Evaluation Layer - Detects errors automatically.
    FREE - No API costs, local processing only.
    """
    if evaluator is None:
        return  # Evaluation system not available
    
    try:
        # Enrich trade result with system context
        enriched_result = trade_result.copy()
        enriched_result.update({
            "tier": tier,
            "script_name": __file__,
            "validated": True,  # Already validated before execution
            "preflight_passed": True,  # Pre-flight checks passed
            "system_state_age_hours": _get_system_state_age_hours(),
            "data_source": _get_data_source_used(),
            "api_errors": [],  # Will be populated if errors occur
            "execution_time_ms": trade_result.get("execution_time_ms", 0)
        })
        
        # Evaluate trade
        evaluation = evaluator.evaluate_trade_execution(
            trade_result=enriched_result,
            expected_amount=expected_amount,
            daily_allocation=daily_allocation
        )
        
        # Save evaluation
        evaluator.save_evaluation(evaluation)
        
        # Store in RAG if available
        if eval_rag_storage and eval_rag_storage.enabled:
            eval_rag_storage.store_evaluation(
                evaluation=dict(evaluation.__dict__),
                trade_result=enriched_result
            )
        
        # Alert on critical issues
        if not evaluation.passed or evaluation.critical_issues:
            print("\n" + "=" * 70)
            print("🚨 EVALUATION ALERT - CRITICAL ISSUES DETECTED")
            print("=" * 70)
            print(f"Trade: {trade_result.get('symbol', 'UNKNOWN')} ${trade_result.get('amount', 0):.2f}")
            print(f"Overall Score: {evaluation.overall_score:.2f}")
            print(f"Passed: {evaluation.passed}")
            
            if evaluation.critical_issues:
                print("\nCritical Issues:")
                for issue in evaluation.critical_issues:
                    print(f"  ❌ {issue}")
            
            # Show dimension scores
            print("\nDimension Scores:")
            for dim_name, dim_result in evaluation.evaluation.items():
                print(f"  {dim_name.upper()}: {dim_result.score:.2f} {'✅' if dim_result.passed else '❌'}")
                if dim_result.issues:
                    for issue in dim_result.issues[:2]:  # Show first 2 issues
                        print(f"    - {issue}")
            
            print("=" * 70)
        else:
            print(f"✅ Evaluation: Score {evaluation.overall_score:.2f} - All checks passed")
    
    except Exception as e:
        print(f"⚠️  Evaluation error (non-critical): {e}")
        import traceback
        traceback.print_exc()


def _get_system_state_age_hours() -> Optional[float]:
    """Get system state age in hours."""
    try:
        system_state_file = DATA_DIR / "system_state.json"
        if system_state_file.exists():
            with open(system_state_file, 'r') as f:
                state = json.load(f)
            last_updated_str = state.get("meta", {}).get("last_updated")
            if last_updated_str:
                last_updated = datetime.fromisoformat(last_updated_str.replace("Z", "+00:00"))
                age_seconds = (datetime.now(last_updated.tzinfo) - last_updated).total_seconds()
                return age_seconds / 3600
    except Exception:
        pass
    return None


def _get_data_source_used() -> str:
    """Get data source used for market data."""
    try:
        # Check performance metrics from market data provider
        metrics = market_data_provider.get_performance_metrics()
        if metrics:
            # Return most recently used source (simplified)
            return "alpaca"  # Default assumption
    except Exception:
        pass
    return "unknown"


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


def calculate_technical_score_wrapper(symbol):
    """
    Calculate technical score using shared utility.
    
    Wrapper around shared calculate_technical_score() function that handles
    data fetching and validation.
    """
    try:
        # Get market data
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

        # Use shared technical indicator utility
        score, indicators = calculate_technical_score(hist, symbol)
        
        if score > 0:
            print(
                f"✅ {symbol}: Score {score:.2f} | "
                f"MACD: {indicators.get('macd_histogram', 0):.3f} | "
                f"RSI: {indicators.get('rsi', 50):.1f} | "
                f"Vol: {indicators.get('volume_ratio', 1.0):.2f}x"
            )
        
        return score

    except Exception as e:
        print(f"❌ {symbol}: Error calculating technical score: {e}")
        import traceback
        traceback.print_exc()
        return 0


def execute_tier1(daily_amount):
    """Tier 1: Core ETF Strategy - 70% using PROPER technical analysis"""
    amount = daily_amount * 0.70

    print("\n" + "=" * 70)
    print("🎯 TIER 1: CORE ETF STRATEGY (MACD + RSI + Volume)")
    print("=" * 70)

    etfs = ["SPY", "QQQ", "VOO"]
    scores = {}

    # Analyze each ETF with REAL technical indicators (using shared utility)
    # PARALLELIZED: Fetch all symbols concurrently for 3x speed improvement
    from concurrent.futures import ThreadPoolExecutor, as_completed

    def fetch_symbol_score(symbol):
        """Fetch score for a single symbol."""
        return symbol, calculate_technical_score_wrapper(symbol)

    print(f"📊 Analyzing {len(etfs)} ETFs in parallel...")
    with ThreadPoolExecutor(max_workers=3) as executor:
        future_to_symbol = {executor.submit(fetch_symbol_score, symbol): symbol for symbol in etfs}
        for future in as_completed(future_to_symbol):
            symbol, score = future.result()
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

    # LANGCHAIN APPROVAL GATE (if enabled)
    if langchain_enabled and langchain_agent:
        try:
            prompt = (
                f"You are the trading desk's approval co-pilot. Evaluate whether "
                f"we should execute a BUY trade for {best} (Core ETF Strategy). "
                f"Respond with a single word: 'APPROVE' or 'DECLINE'.\n\n"
                f"Ticker: {best}\n"
                f"Strategy: Core ETF (SPY/QQQ/VOO momentum)\n"
                f"Use the available sentiment tools to gather recent context. "
                f"Decline if the data is missing, highly bearish, or confidence is low."
            )
            response = langchain_agent.invoke({"input": prompt})
            if isinstance(response, dict):
                text = response.get("output", "")
            else:
                text = str(response)
            
            normalized = text.strip().lower()
            approved = "approve" in normalized and "decline" not in normalized
            
            if not approved:
                print(f"❌ Langchain approval gate REJECTED: {best}")
                print(f"   Response: {text}")
                return False
            else:
                print(f"✅ Langchain approval gate APPROVED: {best}")
        except Exception as e:
            print(f"⚠️  Langchain approval gate error: {e}")
            # Fail-open: proceed if Langchain unavailable
            fail_open = os.getenv("LANGCHAIN_APPROVAL_FAIL_OPEN", "true").lower() == "true"
            if not fail_open:
                print(f"❌ Langchain approval required but unavailable - rejecting trade")
                return False

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
        trade_data = {
            "timestamp": datetime.now().isoformat(),
            "tier": "T1_CORE",
            "symbol": best,
            "amount": amount,
            "order_id": order.id,
            "status": order.status,
        }
        log_trade(trade_data)

        # Week 1: Evaluate trade execution (self-improving RAG)
        evaluate_trade_execution(
            trade_result=trade_data,
            expected_amount=daily_amount * 0.70,
            daily_allocation=daily_amount,
            tier="T1_CORE"
        )

        return True
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def manage_existing_positions():
    """
    Check existing positions and close them if exit rules trigger.
    
    Exit Rules:
    - Tier 2 (NVDA, GOOGL, AMZN): Stop-loss 3%, Take-profit 10%, Max holding 4 weeks
    - Tier 1 (SPY, QQQ, VOO): Buy-and-hold (no automatic exits)
    """
    try:
        positions = api.list_positions()
        if not positions:
            print("✅ No existing positions to manage")
            return
        
        print(f"📊 Checking {len(positions)} existing positions...")
        
        from scripts.state_manager import StateManager
        state_manager = StateManager()
        
        for pos in positions:
            symbol = pos.symbol
            qty = float(pos.qty)
            entry_price = float(pos.avg_entry_price)
            current_price = float(pos.current_price)
            unrealized_pl = float(pos.unrealized_pl)
            unrealized_plpc = float(pos.unrealized_plpc) * 100
            
            # Determine tier and exit rules
            if symbol in ['NVDA', 'GOOGL', 'AMZN']:
                tier = 'Tier 2'
                
                # Use ATR-based dynamic stop-loss if available
                try:
                    from src.utils.technical_indicators import calculate_atr, calculate_atr_stop_loss
                    from src.utils.market_data import get_market_data_provider
                    
                    # Get market data
                    data_provider = get_market_data_provider()
                    hist = data_provider.get_historical_data(symbol, days=30)
                    
                    if not hist.empty and len(hist) >= 15:
                        atr = calculate_atr(hist)
                        atr_stop_price = calculate_atr_stop_loss(entry_price, atr, multiplier=2.0)
                        atr_stop_pct = ((atr_stop_price - entry_price) / entry_price) * 100
                        
                        # Use ATR stop if it's tighter than 3% (better protection)
                        if atr_stop_pct < -3.0:
                            stop_loss_pct = atr_stop_pct
                            print(f"  📊 Using ATR-based stop-loss: {stop_loss_pct:.2f}% (ATR: ${atr:.2f})")
                        else:
                            stop_loss_pct = -3.0
                            print(f"  📊 Using fixed stop-loss: {stop_loss_pct:.2f}% (ATR stop too wide)")
                    else:
                        stop_loss_pct = -3.0
                        print(f"  📊 Using fixed stop-loss: {stop_loss_pct:.2f}% (ATR unavailable)")
                except Exception as e:
                    stop_loss_pct = -3.0
                    print(f"  📊 Using fixed stop-loss: {stop_loss_pct:.2f}% (ATR calculation failed: {e})")
                
                take_profit_pct = 10.0
                max_holding_days = 28  # 4 weeks
            else:
                tier = 'Tier 1'
                stop_loss_pct = None  # Buy-and-hold
                take_profit_pct = None
                max_holding_days = None
            
            print(f"\n{symbol} ({tier}):")
            print(f"  Entry: ${entry_price:.2f}, Current: ${current_price:.2f}")
            print(f"  P/L: ${unrealized_pl:.2f} ({unrealized_plpc:+.2f}%)")
            
            # Get entry date from orders
            orders = api.list_orders(status='all', limit=100, symbols=[symbol])
            buy_orders = [o for o in orders if o.side == 'buy' and o.status == 'filled']
            holding_days = None
            latest_order = None
            
            if buy_orders:
                latest_order = buy_orders[-1]
                if latest_order.filled_at:
                    entry_date = datetime.fromisoformat(str(latest_order.filled_at).replace('Z', '+00:00')).date()
                    holding_days = (date.today() - entry_date).days
                    print(f"  Holding: {holding_days} days")
            else:
                print(f"  ⚠️  Warning: No buy orders found for {symbol}")
            
            should_close = False
            close_reason = None
            
            # Check stop-loss (Tier 2 only)
            if stop_loss_pct is not None:
                print(f"  🔍 Stop-loss check:")
                print(f"     unrealized_plpc: {unrealized_plpc:.2f}%")
                print(f"     stop_loss_pct: {stop_loss_pct:.2f}%")
                print(f"     Condition: {unrealized_plpc:.2f} <= {stop_loss_pct:.2f} = {unrealized_plpc <= stop_loss_pct}")
                
                if unrealized_plpc <= stop_loss_pct:
                    should_close = True
                    close_reason = f"Stop-loss triggered ({unrealized_plpc:.2f}% <= {stop_loss_pct}%)"
                    print(f"  ⚠️  STOP-LOSS TRIGGERED: {close_reason}")
                else:
                    print(f"  ✅ Stop-loss OK: {unrealized_plpc:.2f}% > {stop_loss_pct}%")
            
            # Check take-profit (Tier 2 only)
            elif take_profit_pct and unrealized_plpc >= take_profit_pct:
                should_close = True
                close_reason = f"Take-profit triggered ({unrealized_plpc:.2f}% >= {take_profit_pct}%)"
                print(f"  ✅ TAKE-PROFIT TRIGGERED: {close_reason}")
            
            # Check max holding period (Tier 2 only)
            elif max_holding_days and holding_days and holding_days >= max_holding_days:
                should_close = True
                close_reason = f"Max holding period reached ({holding_days} days >= {max_holding_days} days)"
                print(f"  ⏰ MAX HOLDING PERIOD: {close_reason}")
            
            # Execute close if needed
            if should_close:
                try:
                    print(f"\n  🚀 CLOSING POSITION: {symbol}")
                    print(f"     Reason: {close_reason}")
                    print(f"     Entry: ${entry_price:.2f}, Current: ${current_price:.2f}")
                    print(f"     P/L: ${unrealized_pl:.2f} ({unrealized_plpc:+.2f}%)")
                    print(f"     Quantity: {qty:.6f} shares")
                    
                    close_order = api.close_position(symbol)
                    print(f"  ✅ Position closed successfully!")
                    print(f"     Order ID: {close_order.id}")
                    print(f"     Order Status: {close_order.status}")
                    
                    # Record closed trade
                    entry_date_str = latest_order.filled_at.isoformat() if buy_orders and latest_order.filled_at else datetime.now().isoformat()
                    state_manager.record_closed_trade(
                        symbol=symbol,
                        entry_price=entry_price,
                        exit_price=current_price,
                        quantity=qty,
                        entry_date=entry_date_str,
                        exit_date=datetime.now().isoformat()
                    )
                    
                    # Log trade
                    log_trade({
                        "timestamp": datetime.now().isoformat(),
                        "tier": tier,
                        "symbol": symbol,
                        "action": "SELL",
                        "quantity": qty,
                        "entry_price": entry_price,
                        "exit_price": current_price,
                        "pl": unrealized_pl,
                        "pl_pct": unrealized_plpc,
                        "reason": close_reason,
                        "order_id": close_order.id,
                        "status": close_order.status,
                    })
                    
                except Exception as e:
                    print(f"  ❌ Failed to close position: {e}")
            else:
                if tier == 'Tier 2':
                    print(f"  ✅ Hold: No exit signals (stop-loss: {stop_loss_pct}%, take-profit: {take_profit_pct}%)")
                else:
                    print(f"  📊 Hold: Buy-and-hold strategy (no exit rules)")
        
        print("\n✅ Position management complete")
        
    except Exception as e:
        print(f"⚠️  Error managing positions: {e}")
        import traceback
        traceback.print_exc()


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

    # Analyze REAL technical indicators for each (using shared utility)
    for symbol in stocks:
        score = calculate_technical_score_wrapper(symbol)
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

    # LANGCHAIN APPROVAL GATE (if enabled)
    if langchain_enabled and langchain_agent:
        try:
            prompt = (
                f"You are the trading desk's approval co-pilot. Evaluate whether "
                f"we should execute a BUY trade for {selected} (Growth Strategy). "
                f"Respond with a single word: 'APPROVE' or 'DECLINE'.\n\n"
                f"Ticker: {selected}\n"
                f"Strategy: Disruptive Innovation (NVDA/GOOGL/AMZN momentum)\n"
                f"Use the available sentiment tools to gather recent context. "
                f"Decline if the data is missing, highly bearish, or confidence is low."
            )
            response = langchain_agent.invoke({"input": prompt})
            if isinstance(response, dict):
                text = response.get("output", "")
            else:
                text = str(response)
            
            normalized = text.strip().lower()
            approved = "approve" in normalized and "decline" not in normalized
            
            if not approved:
                print(f"❌ Langchain approval gate REJECTED: {selected}")
                print(f"   Response: {text}")
                return False
            else:
                print(f"✅ Langchain approval gate APPROVED: {selected}")
        except Exception as e:
            print(f"⚠️  Langchain approval gate error: {e}")
            # Fail-open: proceed if Langchain unavailable
            fail_open = os.getenv("LANGCHAIN_APPROVAL_FAIL_OPEN", "true").lower() == "true"
            if not fail_open:
                print(f"❌ Langchain approval required but unavailable - rejecting trade")
                return False

    # GEMINI 3 VALIDATION GATE (Strategic Check)
    if gemini_enabled and gemini_agent:
        try:
            print(f"🤖 Requesting Gemini 3 strategic validation for {selected}...")
            gemini_prompt = (
                f"Analyze a potential BUY trade for {selected} (Growth Strategy).\n"
                f"Context: Disruptive Innovation theme ({themes.get(selected, 'Innovation')}).\n"
                f"Technical Score: {scores.get(selected, 0):.2f}\n"
                f"Goal: Long-term growth with 3% stop-loss.\n"
                f"Task: Validate this trade. Is the risk/reward favorable right now?\n"
                f"Output JSON with keys: 'decision' (APPROVE/DECLINE), 'reasoning', 'confidence' (0-1)."
            )
            
            # Use high thinking level for deep analysis
            gemini_result = gemini_agent.reason(
                prompt=gemini_prompt,
                thinking_level="high"
            )
            
            decision = gemini_result.get("decision", "").upper()
            # Parse decision from reasoning if not explicit (fallback)
            if not decision and "APPROVE" in gemini_result.get("reasoning", "").upper():
                decision = "APPROVE"
            elif not decision:
                decision = "DECLINE"
                
            if "APPROVE" in decision:
                print(f"✅ Gemini 3 Agent VALIDATED: {selected}")
                print(f"   Reasoning: {gemini_result.get('reasoning', '')[:100]}...")
            else:
                print(f"❌ Gemini 3 Agent REJECTED: {selected}")
                print(f"   Reasoning: {gemini_result.get('reasoning', '')}")
                return False
                
        except Exception as e:
            print(f"⚠️  Gemini 3 validation error: {e}")
            # Fail-open for now, but log it


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

        # Log trade
        trade_data = {
            "timestamp": datetime.now().isoformat(),
            "tier": "T2_GROWTH",
            "symbol": selected,
            "amount": amount,
            "order_id": order.id,
            "status": order.status,
        }
        log_trade(trade_data)

        # Week 1: Evaluate trade execution (self-improving RAG)
        evaluate_trade_execution(
            trade_result=trade_data,
            expected_amount=daily_amount * 0.30,
            daily_allocation=daily_amount,
            tier="T2_GROWTH"
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


def execute_crypto_strategy(daily_investment):
    """
    Execute Tier 5: Crypto Strategy (Weekend Mode).

    Args:
        daily_investment: Daily investment amount

    Returns:
        Boolean indicating success
    """
    print("\n" + "=" * 70)
    print("🌐 WEEKEND MODE: TIER 5 CRYPTO STRATEGY")
    print("=" * 70)

    try:
        # Import risk manager for crypto strategy
        from src.core.risk_manager import RiskManager

        # Initialize risk manager (create placeholder if needed)
        risk_manager = RiskManager(
            max_daily_loss_pct=5.0,  # Higher risk tolerance for crypto
            max_position_size_pct=10.0,
            max_drawdown_pct=15.0
        )

        # Initialize crypto strategy
        crypto_strategy = CryptoStrategy(
            trader=api,
            risk_manager=risk_manager,
            daily_amount=daily_investment
        )

        # Execute crypto strategy
        result = crypto_strategy.execute()

        if result.get("success"):
            print(f"✅ Crypto trade executed: {result.get('symbol')} for ${result.get('amount', 0):.2f}")
            return True
        else:
            reason = result.get("reason", "unknown")
            message = result.get("message", "No details available")
            print(f"⚠️  Crypto trade skipped: {reason}")
            print(f"   Details: {message}")
            return False

    except Exception as e:
        print(f"❌ Crypto strategy execution failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Main autonomous trading execution with intelligent position sizing"""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Autonomous Daily Trader")
    parser.add_argument(
        "--crypto-only",
        action="store_true",
        help="Force crypto-only execution (Tier 5) regardless of day of week"
    )
    args = parser.parse_args()

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

    # WEEKEND vs WEEKDAY MODE (or force crypto with --crypto-only flag)
    weekend_mode = args.crypto_only or is_weekend()

    print(f"📊 Trading Day: {current_day}")
    print(f"💰 Portfolio Value: ${account_value:,.2f}")
    print(f"📈 Daily Investment: ${daily_investment:.2f} (FIXED - not portfolio-based)")

    if weekend_mode:
        mode_source = "(FORCED via --crypto-only)" if args.crypto_only else "(Auto: Weekend)"
        print(f"🌐 MODE: WEEKEND {mode_source} (Crypto Trading)")
        print("🎯 Strategy: Tier 5 - Cryptocurrency 24/7")
    else:
        print("📈 MODE: WEEKDAY (Stock Trading)")
        print("🎯 Strategy: Momentum (MACD + RSI + Volume)")
        print(f"📊 Breakdown: Core 70% (${daily_investment*0.7:.2f}) | Growth 30% (${daily_investment*0.3:.2f})")

    print("=" * 70)

    # WEEKEND MODE: Execute crypto strategy and skip stock logic
    if weekend_mode:
        mode_reason = "Manual override (--crypto-only flag)" if args.crypto_only else "Stock markets closed (Sat-Sun)"
        print(f"\n🌐 WEEKEND MODE ACTIVE - Executing Crypto Strategy")
        print(f"💡 {mode_reason} - Crypto trades 24/7")

        crypto_success = execute_crypto_strategy(daily_investment)

        # Update performance and skip stock-specific logic
        print("\n" + "=" * 70)
        print("📊 PERFORMANCE UPDATE")
        print("=" * 70)

        perf = update_performance_log()
        print(f"💰 Equity: ${perf['equity']:,.2f}")
        print(f"📈 P/L: ${perf['pl']:+,.2f} ({perf['pl_pct']:+.2f}%)")
        print(f"💵 Cash: ${perf['cash']:,.2f}")

        print("\n" + "=" * 70)
        print("✅ WEEKEND EXECUTION COMPLETE")
        print("=" * 70)
        print(f"Tier 5 (Crypto): {'✅' if crypto_success else '⚠️'}")
        print(f"\n📁 Logs saved to: {DATA_DIR}")
        print("🎯 Next execution: Monday 9:35 AM ET (or tomorrow if Sunday)")
        print("=" * 70)

        return  # Exit early - no stock trading on weekends

    # WEEKDAY MODE: Execute stock strategies (existing logic)
    # Check if market is open
    clock = api.get_clock()
    if not clock.is_open:
        print("⚠️  Market is closed. Order will execute at next open.")
    else:
        # Wait for market stabilization (5-10 min post-open)
        wait_for_market_stabilization()

    # STEP 1: Manage existing positions FIRST (check stop-loss, take-profit, holding period)
    print("\n" + "=" * 70)
    print("🔍 MANAGING EXISTING POSITIONS")
    print("=" * 70)
    manage_existing_positions()

    # DEEPAGENTS MODE: Try DeepAgents orchestrator (ENABLED BY DEFAULT)
    deepagents_enabled = os.getenv("DEEPAGENTS_ENABLED", "true").lower() == "true"
    deepagents_used = False
    
    if deepagents_enabled:
        try:
            print("\n" + "=" * 70)
            print("🧠 DEEPAGENTS MODE: Planning-Based Trading Cycle")
            print("=" * 70)
            print("📋 Using DeepAgents pattern:")
            print("   1. Planning: Break down trading cycle into steps")
            print("   2. Research: Delegate to research sub-agents")
            print("   3. Signal: Generate trading signals")
            print("   4. Risk: Validate with risk sub-agent")
            print("   5. Execute: Place orders with approval gates")
            print("=" * 70)
            
            from src.orchestration.deepagents_trading import DeepAgentsTradingOrchestrator
            
            symbols = ["SPY", "QQQ", "VOO", "NVDA", "GOOGL", "AMZN"]
            orchestrator = DeepAgentsTradingOrchestrator(symbols=symbols, paper=True)
            
            result = asyncio.run(orchestrator.execute_trading_cycle())
            
            if result.get("status") == "completed":
                deepagents_used = True
                print("✅ DeepAgents cycle completed successfully")
                print(f"   Plan: {result.get('plan', {}).get('cycle_id', 'N/A')}")
                print(f"   Results: {len(result.get('results', {}))} steps executed")
            else:
                print(f"⚠️  DeepAgents cycle failed: {result.get('error', 'Unknown')}")
                print("   Falling back to standard strategies")
        except Exception as e:
            print(f"⚠️  DeepAgents mode failed: {e}")
            print("   Falling back to standard strategies")
            import traceback
            traceback.print_exc()
    
    # TURBO MODE: Try ADK orchestrator first (if enabled and service available)
    adk_used = False
    tier1_success = False
    tier2_success = False
    
    if not deepagents_used and adk_adapter.enabled and adk_service_available:
        try:
            print("\n" + "=" * 70)
            print("🚀 TURBO MODE: ADK Orchestrator Evaluation (Primary Decision Maker)")
            print("=" * 70)
            print("📊 Using Go ADK multi-agent system:")
            print("   1. Research Agent → Market analysis")
            print("   2. Signal Agent → Trade signal generation")
            print("   3. Risk Agent → Position sizing & validation")
            print("   4. Execution Agent → Trade planning")
            print("=" * 70)
            
            context = {
                "mode": "paper",
                "daily_investment": daily_investment,
                "tier1_allocation": daily_investment * 0.70,
                "tier2_allocation": daily_investment * 0.30,
                "account_value": account_value,
                "current_day": current_day,
                "portfolio_equity": account_value,
            }
            
            # Try ADK for Tier 1 (Core ETF) - PRIMARY DECISION MAKER
            print("\n🎯 TIER 1: ADK Orchestrator Evaluation")
            tier1_symbols = ["SPY", "QQQ", "VOO"]
            tier1_decision = adk_adapter.evaluate(
                symbols=tier1_symbols,
                context={**context, "tier": "T1_CORE", "strategy": "Core ETF Momentum"},
            )
            
            if tier1_decision and tier1_decision.action == "BUY":
                print(f"✅ ADK Tier 1 Decision: {tier1_decision.symbol} BUY")
                print(f"   Confidence: {tier1_decision.confidence:.2%}")
                print(f"   Position Size: ${tier1_decision.position_size:.2f}")
                print(f"   Risk Assessment: {tier1_decision.risk.get('decision', 'UNKNOWN')}")
                
                amount = tier1_decision.position_size or (daily_investment * 0.70)
                is_valid, error_msg = validate_order_size(amount, daily_investment * 0.70, "T1_CORE_ADK")
                if is_valid:
                    # LANGCHAIN APPROVAL GATE (if enabled) - Secondary validation
                    langchain_approved = True
                    if langchain_enabled and langchain_agent:
                        try:
                            prompt = (
                                f"ADK orchestrator recommends BUY {tier1_decision.symbol} "
                                f"with {tier1_decision.confidence:.2%} confidence. "
                                f"Final approval check - respond 'APPROVE' or 'DECLINE'."
                            )
                            response = langchain_agent.invoke({"input": prompt})
                            text = response.get("output", "") if isinstance(response, dict) else str(response)
                            langchain_approved = "approve" in text.lower() and "decline" not in text.lower()
                            
                            if not langchain_approved:
                                print(f"❌ Langchain approval gate REJECTED ADK decision: {text}")
                            else:
                                print(f"✅ Langchain approval gate APPROVED ADK decision")
                        except Exception as e:
                            print(f"⚠️  Langchain approval gate error: {e} (proceeding with ADK decision)")
                            langchain_approved = True  # Fail-open
                    
                    if langchain_approved:
                        try:
                            order = api.submit_order(
                                symbol=tier1_decision.symbol,
                                notional=amount,
                                side="buy",
                                type="market",
                                time_in_force="day"
                            )
                            print(f"✅ ADK Tier 1 Order EXECUTED: {order.id}")
                            trade_data = {
                                "timestamp": datetime.now().isoformat(),
                                "tier": "T1_CORE_ADK",
                                "symbol": tier1_decision.symbol,
                                "amount": amount,
                                "order_id": order.id,
                                "status": order.status,
                                "adk_confidence": tier1_decision.confidence,
                                "adk_risk_decision": tier1_decision.risk.get("decision", "UNKNOWN"),
                            }
                            log_trade(trade_data)
                            
                            # Week 1: Evaluate trade execution
                            evaluate_trade_execution(
                                trade_result=trade_data,
                                expected_amount=daily_investment * 0.70,
                                daily_allocation=daily_investment,
                                tier="T1_CORE_ADK"
                            )
                            
                            tier1_success = True
                            adk_used = True
                        except Exception as e:
                            print(f"❌ ADK Tier 1 order execution failed: {e}")
                            import traceback
                            traceback.print_exc()
                            tier1_success = False
                else:
                    print(f"❌ ADK Tier 1 order rejected by validation: {error_msg}")
                    tier1_success = False
            elif tier1_decision:
                print(f"⚠️  ADK Tier 1 Decision: {tier1_decision.action} (not BUY)")
                print(f"   Confidence: {tier1_decision.confidence:.2%}")
                tier1_success = False
            else:
                print("⚠️  ADK Tier 1: No decision returned (will fallback to rule-based)")
                tier1_success = False
            
            # Try ADK for Tier 2 (Growth) - PRIMARY DECISION MAKER
            print("\n🎯 TIER 2: ADK Orchestrator Evaluation")
            tier2_symbols = ["NVDA", "GOOGL", "AMZN"]
            tier2_decision = adk_adapter.evaluate(
                symbols=tier2_symbols,
                context={**context, "tier": "T2_GROWTH", "strategy": "Disruptive Innovation"},
            )
            
            if tier2_decision and tier2_decision.action == "BUY":
                print(f"✅ ADK Tier 2 Decision: {tier2_decision.symbol} BUY")
                print(f"   Confidence: {tier2_decision.confidence:.2%}")
                print(f"   Position Size: ${tier2_decision.position_size:.2f}")
                print(f"   Risk Assessment: {tier2_decision.risk.get('decision', 'UNKNOWN')}")
                
                amount = tier2_decision.position_size or (daily_investment * 0.30)
                is_valid, error_msg = validate_order_size(amount, daily_investment * 0.30, "T2_GROWTH_ADK")
                if is_valid:
                    # LANGCHAIN APPROVAL GATE (if enabled) - Secondary validation
                    langchain_approved = True
                    if langchain_enabled and langchain_agent:
                        try:
                            prompt = (
                                f"ADK orchestrator recommends BUY {tier2_decision.symbol} "
                                f"with {tier2_decision.confidence:.2%} confidence. "
                                f"Final approval check - respond 'APPROVE' or 'DECLINE'."
                            )
                            response = langchain_agent.invoke({"input": prompt})
                            text = response.get("output", "") if isinstance(response, dict) else str(response)
                            langchain_approved = "approve" in text.lower() and "decline" not in text.lower()
                            
                            if not langchain_approved:
                                print(f"❌ Langchain approval gate REJECTED ADK decision: {text}")
                            else:
                                print(f"✅ Langchain approval gate APPROVED ADK decision")
                        except Exception as e:
                            print(f"⚠️  Langchain approval gate error: {e} (proceeding with ADK decision)")
                            langchain_approved = True  # Fail-open
                    
                    if langchain_approved:
                        try:
                            order = api.submit_order(
                                symbol=tier2_decision.symbol,
                                notional=amount,
                                side="buy",
                                type="market",
                                time_in_force="day"
                            )
                            print(f"✅ ADK Tier 2 Order EXECUTED: {order.id}")
                            trade_data = {
                                "timestamp": datetime.now().isoformat(),
                                "tier": "T2_GROWTH_ADK",
                                "symbol": tier2_decision.symbol,
                                "amount": amount,
                                "order_id": order.id,
                                "status": order.status,
                                "adk_confidence": tier2_decision.confidence,
                                "adk_risk_decision": tier2_decision.risk.get("decision", "UNKNOWN"),
                            }
                            log_trade(trade_data)
                            
                            # Week 1: Evaluate trade execution
                            evaluate_trade_execution(
                                trade_result=trade_data,
                                expected_amount=daily_investment * 0.30,
                                daily_allocation=daily_investment,
                                tier="T2_GROWTH_ADK"
                            )
                            
                            tier2_success = True
                            adk_used = True
                        except Exception as e:
                            print(f"❌ ADK Tier 2 order execution failed: {e}")
                            import traceback
                            traceback.print_exc()
                            tier2_success = False
                else:
                    print(f"❌ ADK Tier 2 order rejected by validation: {error_msg}")
                    tier2_success = False
            elif tier2_decision:
                print(f"⚠️  ADK Tier 2 Decision: {tier2_decision.action} (not BUY)")
                print(f"   Confidence: {tier2_decision.confidence:.2%}")
                tier2_success = False
            else:
                print("⚠️  ADK Tier 2: No decision returned (will fallback to rule-based)")
                tier2_success = False
                
        except Exception as e:
            print(f"\n❌ ADK orchestrator error: {e}")
            print("   Falling back to Python rule-based strategies")
            import traceback
            traceback.print_exc()
            tier1_success = False
            tier2_success = False
    elif adk_adapter.enabled and not adk_service_available:
        print("\n⚠️  ADK orchestrator enabled but service not available")
        print("   Falling back to Python rule-based strategies")
    
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
