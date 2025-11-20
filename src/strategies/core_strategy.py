"""
Core Trading Strategy - Tier 1 (60% Allocation)

Low-risk momentum index investing with AI sentiment overlay.
Target: 8-12% annual returns | Risk: LOW

Strategy Flow:
1. Query AI (MultiLLMAnalyzer) for market sentiment analysis
2. Calculate momentum scores for SPY, QQQ, VOO using multi-period returns
3. Select ETF with highest momentum score (weighted by sentiment)
4. Execute daily $6 (configurable) purchase via Alpaca API
5. Set 5% trailing stop-loss on all positions
6. Monthly rebalancing check and execution
7. Risk management via RiskManager with circuit breakers

Key Features:
- Multi-LLM ensemble sentiment analysis (Claude, GPT-4, Gemini)
- Momentum scoring with volatility adjustment and Sharpe ratio
- Fractional share trading via Alpaca API
- Automated stop-loss management
- Risk controls: max daily loss (2%), max drawdown (10%)
- Comprehensive performance tracking and metrics
- Monthly portfolio rebalancing to maintain target allocations

Dependencies:
- src.core.multi_llm_analysis.MultiLLMAnalyzer
- src.core.alpaca_trader.AlpacaTrader
- src.core.risk_manager.RiskManager

Author: Trading System
Created: 2025-10-28
Updated: 2025-10-28
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

import pandas as pd
import numpy as np
import yfinance as yf

# Import project modules
from src.core.multi_llm_analysis import MultiLLMAnalyzer
from src.core.alpaca_trader import AlpacaTrader
from src.core.risk_manager import RiskManager
from src.utils.sentiment_loader import (
    load_latest_sentiment,
    get_ticker_sentiment,
    get_market_regime,
    get_sentiment_history,
)


# Configure logging
logger = logging.getLogger(__name__)


class MarketSentiment(Enum):
    """Market sentiment classification."""

    VERY_BULLISH = "very_bullish"
    BULLISH = "bullish"
    NEUTRAL = "neutral"
    BEARISH = "bearish"
    VERY_BEARISH = "very_bearish"


@dataclass
class MomentumScore:
    """Data class for ETF momentum analysis."""

    symbol: str
    score: float
    returns_1m: float
    returns_3m: float
    returns_6m: float
    volatility: float
    sharpe_ratio: float
    rsi: float
    macd_value: float
    macd_signal: float
    macd_histogram: float
    volume_ratio: float
    sentiment_boost: float
    timestamp: datetime


@dataclass
class TradeOrder:
    """Data class for trade order details."""

    symbol: str
    action: str  # 'buy' or 'sell'
    quantity: float
    amount: float
    price: Optional[float]
    order_type: str
    stop_loss: Optional[float]
    timestamp: datetime
    reason: str


class CoreStrategy:
    """
    Core trading strategy implementing low-risk momentum index investing
    with AI sentiment overlay.

    This strategy:
    - Focuses on major index ETFs (SPY, QQQ, VOO)
    - Uses momentum indicators to select the best performer
    - Incorporates AI sentiment analysis for market conditions
    - Executes daily dollar-cost averaging
    - Implements risk management with trailing stop-loss
    - Performs monthly portfolio rebalancing

    Attributes:
        daily_allocation (float): Dollar amount to invest daily
        etf_universe (List[str]): List of ETFs to analyze
        lookback_periods (Dict[str, int]): Momentum calculation periods
        stop_loss_pct (float): Trailing stop-loss percentage
        rebalance_threshold (float): Threshold for triggering rebalance
        last_rebalance_date (datetime): Last rebalancing timestamp
        current_holdings (Dict[str, float]): Current position sizes
    """

    # Default ETF universe for Tier 1 strategy
    DEFAULT_ETF_UNIVERSE = ["SPY", "QQQ", "VOO"]

    # Momentum calculation periods (in days)
    LOOKBACK_PERIODS = {"1month": 21, "3month": 63, "6month": 126}

    # Momentum weight distribution
    MOMENTUM_WEIGHTS = {
        "1month": 0.5,  # 50% weight to recent performance
        "3month": 0.3,  # 30% weight to medium-term
        "6month": 0.2,  # 20% weight to long-term
    }

    # RSI parameters
    RSI_PERIOD = 14
    RSI_OVERSOLD = 30
    RSI_OVERBOUGHT = 70

    # MACD parameters
    MACD_FAST_PERIOD = 12
    MACD_SLOW_PERIOD = 26
    MACD_SIGNAL_PERIOD = 9

    # Risk parameters
    DEFAULT_STOP_LOSS_PCT = 0.05  # 5% trailing stop (fallback)
    ATR_STOP_MULTIPLIER = 2.0  # ATR multiplier for dynamic stops
    USE_ATR_STOPS = True  # Use ATR-based stops (more adaptive)
    REBALANCE_THRESHOLD = 0.15  # 15% deviation triggers rebalance
    REBALANCE_FREQUENCY_DAYS = 30  # Monthly rebalancing

    def __init__(
        self,
        daily_allocation: float = 6.0,
        etf_universe: Optional[List[str]] = None,
        stop_loss_pct: float = DEFAULT_STOP_LOSS_PCT,
        use_sentiment: bool = True,
    ):
        """
        Initialize the Core Strategy.

        Args:
            daily_allocation: Daily investment amount in dollars (default: $6)
            etf_universe: List of ETF symbols to analyze (default: SPY, QQQ, VOO)
            stop_loss_pct: Trailing stop-loss percentage (default: 5%)
            use_sentiment: Whether to use AI sentiment analysis (default: True)

        Raises:
            ValueError: If daily_allocation is non-positive
        """
        if daily_allocation <= 0:
            raise ValueError(
                f"daily_allocation must be positive, got {daily_allocation}"
            )

        self.daily_allocation = daily_allocation
        self.etf_universe = etf_universe or self.DEFAULT_ETF_UNIVERSE
        self.stop_loss_pct = stop_loss_pct
        self.use_sentiment = use_sentiment

        # Strategy state
        self.current_holdings: Dict[str, float] = {}
        self.last_rebalance_date: Optional[datetime] = None
        self.total_invested: float = 0.0
        self.total_value: float = 0.0

        # Performance tracking
        self.daily_returns: List[float] = []
        self.trades_executed: List[TradeOrder] = []
        self.momentum_history: List[MomentumScore] = []

        # Initialize dependencies
        try:
            self.llm_analyzer = (
                MultiLLMAnalyzer(use_async=False) if use_sentiment else None
            )
            self.alpaca_trader = AlpacaTrader(paper=True)
            self.risk_manager = RiskManager(
                max_daily_loss_pct=2.0,
                max_position_size_pct=20.0,  # 20% for low-risk tier
                max_drawdown_pct=10.0,
                max_consecutive_losses=5,
            )
            logger.info("Successfully initialized core dependencies")
        except Exception as e:
            logger.warning(f"Failed to initialize some dependencies: {e}")
            self.llm_analyzer = None
            self.alpaca_trader = None
            self.risk_manager = None

        logger.info(
            f"CoreStrategy initialized: daily_allocation=${daily_allocation}, "
            f"etf_universe={self.etf_universe}, stop_loss={stop_loss_pct*100}%"
        )

    def execute_daily(self) -> Optional[TradeOrder]:
        """
        Execute the daily trading routine.

        This is the main entry point that orchestrates:
        1. Market sentiment analysis
        2. Momentum calculation
        3. ETF selection
        4. Order execution
        5. Risk management

        Returns:
            TradeOrder if an order was placed, None otherwise

        Raises:
            Exception: If critical trading error occurs
        """
        logger.info("=" * 80)
        logger.info("Starting daily strategy execution")
        logger.info(f"Timestamp: {datetime.now().isoformat()}")
        logger.info(f"Daily allocation: ${self.daily_allocation}")

        try:
            # Step 1: Get market sentiment from AI
            sentiment = self._get_market_sentiment()
            logger.info(f"Market sentiment: {sentiment.value}")

            # Step 2: Check if we should pause trading based on sentiment
            if sentiment == MarketSentiment.VERY_BEARISH:
                logger.warning(
                    "Very bearish sentiment detected - pausing new purchases"
                )
                return None

            # Step 3: Calculate momentum scores for all ETFs
            momentum_scores = self._calculate_all_momentum_scores(sentiment)

            # Step 4: Select best ETF (may skip if all fail hard filters)
            try:
                best_etf = self.select_best_etf(momentum_scores)
                logger.info(f"Selected ETF: {best_etf}")
            except ValueError as e:
                logger.warning(f"No valid ETF selection today: {e}")
                logger.info("SKIPPING TRADE - Will try again tomorrow")
                return None

            # Step 4.5: Gemini 3 AI Validation (if enabled)
            if self.gemini3_enabled and self._gemini3_integration and self._gemini3_integration.enabled:
                try:
                    logger.info("Validating trade with Gemini 3 AI...")
                    market_context = {
                        "symbol": best_etf,
                        "sentiment": sentiment.value,
                        "momentum_scores": {ms.symbol: ms.score for ms in momentum_scores},
                        "timestamp": datetime.now().isoformat(),
                    }
                    
                    gemini_recommendation = self._gemini3_integration.get_trading_recommendation(
                        symbol=best_etf,
                        market_context=market_context,
                        thinking_level="high",  # Deep analysis for trade validation
                    )
                    
                    if gemini_recommendation.get("decision"):
                        decision = gemini_recommendation["decision"]
                        action = decision.get("action", "HOLD")
                        confidence = decision.get("confidence", 0.0)
                        
                        if action != "BUY" or confidence < 0.6:
                            logger.warning(
                                f"Gemini 3 AI rejected trade: {action} (confidence: {confidence:.2f})"
                            )
                            logger.info(f"Gemini reasoning: {decision.get('reasoning', 'N/A')}")
                            logger.info("SKIPPING TRADE - AI validation failed")
                            return None
                        else:
                            logger.info(
                                f"Gemini 3 AI approved trade: {action} (confidence: {confidence:.2f})"
                            )
                except Exception as e:
                    logger.warning(f"Gemini 3 validation error (proceeding): {e}")
                    # Fail-open: continue with trade if Gemini 3 unavailable

            # Step 5: Get current price
            current_price = self._get_current_price(best_etf)
            if current_price is None:
                logger.error(f"Failed to get price for {best_etf}")
                return None

            # Step 6: Calculate quantity
            quantity = self.daily_allocation / current_price

            # Step 7: Risk validation
            if not self._validate_trade(best_etf, quantity, current_price, sentiment):
                logger.warning("Trade failed risk validation")
                return None

            # Step 8: Create order
            order = self._create_buy_order(
                symbol=best_etf,
                quantity=quantity,
                price=current_price,
                sentiment=sentiment,
            )

            # Step 9: Execute order via Alpaca
            if self.alpaca_trader:
                try:
                    executed_order = self.alpaca_trader.execute_order(
                        symbol=best_etf, amount_usd=self.daily_allocation, side="buy", tier="T1_CORE"
                    )
                    logger.info(f"Alpaca order executed: {executed_order['id']}")

                    # Set stop-loss order
                    if order.stop_loss:
                        self.alpaca_trader.set_stop_loss(
                            symbol=best_etf, qty=quantity, stop_price=order.stop_loss
                        )
                        logger.info(f"Stop-loss set at ${order.stop_loss:.2f}")
                except Exception as e:
                    logger.error(f"Failed to execute order via Alpaca: {e}")
                    return None

            # Step 10: Update state
            self._update_holdings(best_etf, quantity)
            self.total_invested += self.daily_allocation
            self.trades_executed.append(order)

            logger.info(f"Order executed successfully: {order}")
            logger.info(f"Total invested to date: ${self.total_invested:.2f}")

            # Step 11: Check if rebalancing needed
            if self.should_rebalance():
                logger.info("Rebalancing required - will execute after market close")

            return order

        except Exception as e:
            logger.error(f"Error in daily execution: {str(e)}", exc_info=True)
            raise

    def calculate_momentum(self, symbol: str) -> float:
        """
        Calculate composite momentum score for a given ETF.

        The momentum score is a weighted combination of:
        - Multi-period returns (1m, 3m, 6m)
        - Volatility-adjusted performance
        - Sharpe ratio
        - RSI indicator
        - Risk-adjusted metrics

        Args:
            symbol: ETF ticker symbol

        Returns:
            Composite momentum score (0-100 scale)

        Raises:
            ValueError: If unable to calculate momentum for symbol
        """
        logger.info(f"Calculating momentum for {symbol}")

        hist = None
        lookback_days = (
            max(self.LOOKBACK_PERIODS.values()) + 20
        )  # Extra for calculations
        end_date = datetime.now()
        start_date = end_date - timedelta(days=lookback_days)

        # Try yfinance first
        try:
            ticker = yf.Ticker(symbol)
            hist = ticker.history(start=start_date, end=end_date)

            if hist.empty or len(hist) < lookback_days * 0.7:
                logger.warning(f"yfinance returned insufficient data for {symbol}, trying Alpaca API")
                hist = None
        except Exception as e:
            logger.warning(f"yfinance failed for {symbol}: {str(e)}, trying Alpaca API fallback")
            hist = None

        # Fallback to Alpaca API if yfinance failed
        if hist is None or hist.empty:
            try:
                if self.alpaca_trader:
                    logger.info(f"Fetching historical data from Alpaca for {symbol}")
                    bars = self.alpaca_trader.get_historical_bars(
                        symbol=symbol,
                        timeframe="1Day",
                        limit=lookback_days
                    )
                    
                    if bars and len(bars) >= lookback_days * 0.7:
                        # Convert Alpaca bars to pandas DataFrame
                        import pandas as pd
                        dates = [pd.Timestamp(bar['timestamp']) for bar in bars]
                        hist = pd.DataFrame({
                            'Open': [bar['open'] for bar in bars],
                            'High': [bar['high'] for bar in bars],
                            'Low': [bar['low'] for bar in bars],
                            'Close': [bar['close'] for bar in bars],
                            'Volume': [bar['volume'] for bar in bars]
                        }, index=dates)
                        hist.index.name = 'Date'
                        hist.sort_index(inplace=True)
                        logger.info(f"Successfully loaded {len(hist)} bars from Alpaca for {symbol}")
                    else:
                        raise ValueError(f"Alpaca returned insufficient data for {symbol}")
                else:
                    raise ValueError(f"No Alpaca trader available and yfinance failed for {symbol}")
            except Exception as e:
                logger.error(f"Alpaca API fallback also failed for {symbol}: {str(e)}")
                raise ValueError(f"Failed to fetch historical data for {symbol} from both yfinance and Alpaca: {str(e)}") from e

        if hist.empty or len(hist) < lookback_days * 0.7:
            raise ValueError(f"Insufficient data for {symbol} (got {len(hist)} bars, need {int(lookback_days * 0.7)})")

        # Calculate returns for different periods
        returns_1m = self._calculate_period_return(
            hist, self.LOOKBACK_PERIODS["1month"]
        )
        returns_3m = self._calculate_period_return(
            hist, self.LOOKBACK_PERIODS["3month"]
        )
        returns_6m = self._calculate_period_return(
            hist, self.LOOKBACK_PERIODS["6month"]
        )

        # Calculate volatility (annualized)
        daily_returns = hist["Close"].pct_change().dropna()
        volatility = daily_returns.std() * np.sqrt(252)

        # Calculate Sharpe ratio (assuming 4% risk-free rate)
        risk_free_rate = 0.04
        excess_return = returns_6m - risk_free_rate
        sharpe_ratio = excess_return / volatility if volatility > 0 else 0

        # Calculate RSI
        rsi = self._calculate_rsi(hist["Close"], self.RSI_PERIOD)

        # Weighted momentum score
        momentum_score = (
            returns_1m * self.MOMENTUM_WEIGHTS["1month"] * 100
            + returns_3m * self.MOMENTUM_WEIGHTS["3month"] * 100
            + returns_6m * self.MOMENTUM_WEIGHTS["6month"] * 100
        )

        # Adjust for volatility (penalize high volatility)
        volatility_penalty = volatility * 10  # Scale penalty
        momentum_score -= volatility_penalty

        # Adjust for Sharpe ratio (reward better risk-adjusted returns)
        sharpe_bonus = sharpe_ratio * 5
        momentum_score += sharpe_bonus

        # HARD FILTERS - Reject entries that don't meet criteria
        # Calculate MACD first for filtering
        macd_value, macd_signal, macd_histogram = self._calculate_macd(hist["Close"])

        # HARD FILTER 1: Reject bearish MACD (histogram below zero)
        if macd_histogram < 0:
            logger.warning(
                f"{symbol} REJECTED - Bearish MACD histogram ({macd_histogram:.4f}). "
                f"Trend is down, not entering position."
            )
            return -1  # Return invalid score to filter out

        # HARD FILTER 2: Reject overbought RSI (>70)
        if rsi > 70:
            logger.warning(
                f"{symbol} REJECTED - Overbought RSI ({rsi:.2f}). "
                f"Too extended, high reversal risk."
            )
            return -1  # Return invalid score to filter out
        
        # HARD FILTER 3: Reject if price > 20-day MA (wait for pullback)
        # CTO Decision: Prevent entries at peaks (like SPY -4.44% loss)
        ma_20 = hist["Close"].rolling(window=20).mean().iloc[-1]
        current_price = hist["Close"].iloc[-1]
        price_vs_ma_pct = ((current_price - ma_20) / ma_20) * 100
        
        if current_price > ma_20 * 1.02:  # Price > 2% above 20-day MA
            logger.warning(
                f"{symbol} REJECTED - Price ${current_price:.2f} is {price_vs_ma_pct:.2f}% above 20-day MA ${ma_20:.2f}. "
                f"Waiting for pullback entry to avoid buying at peak."
            )
            return -1  # Return invalid score to filter out
        
        # RSI adjustment (bonus if in healthy range, prefer pullbacks)
        if self.RSI_OVERSOLD < rsi < 50:  # Prefer RSI < 50 for pullback entries
            momentum_score += 5
        elif self.RSI_OVERSOLD < rsi < 60:
            momentum_score += 3

        # MACD adjustment (momentum confirmation for bullish signals)
        if macd_histogram > 0:  # Bullish MACD (passed hard filter)
            momentum_score += 8

        # Volume confirmation (high volume = stronger signal)
        volume_ratio = self._calculate_volume_ratio(hist)
        if volume_ratio > 1.5:  # Volume 50% above average (high conviction)
            momentum_score += 10
        elif volume_ratio > 1.2:  # Volume 20% above average
            momentum_score += 5
        elif volume_ratio < 0.5:  # Volume 50% below average (low conviction)
            momentum_score -= 10

        # Normalize to 0-100 scale
        momentum_score = max(0, min(100, momentum_score))

        logger.info(
            f"{symbol} momentum: {momentum_score:.2f} "
            f"(1m: {returns_1m*100:.2f}%, 3m: {returns_3m*100:.2f}%, "
            f"6m: {returns_6m*100:.2f}%, vol: {volatility:.2f}, "
            f"sharpe: {sharpe_ratio:.2f}, rsi: {rsi:.2f}, "
            f"macd: {macd_value:.4f}, signal: {macd_signal:.4f}, "
            f"histogram: {macd_histogram:.4f}, vol_ratio: {volume_ratio:.2f})"
        )

        return momentum_score

    def select_best_etf(
        self, momentum_scores: Optional[List[MomentumScore]] = None
    ) -> str:
        """
        Select the ETF with the highest momentum score.

        Args:
            momentum_scores: Pre-calculated momentum scores (optional)

        Returns:
            Symbol of the best ETF to purchase

        Raises:
            ValueError: If no valid ETF can be selected
        """
        logger.info("Selecting best ETF from universe")

        # Calculate scores if not provided
        if momentum_scores is None:
            sentiment = self._get_market_sentiment()
            momentum_scores = self._calculate_all_momentum_scores(sentiment)

        # If no momentum scores available, DO NOT TRADE
        if not momentum_scores:
            logger.warning(
                "🚫 NO VALID ENTRIES TODAY - All symbols rejected by hard filters"
            )
            logger.warning(
                "Either all symbols have bearish MACD or overbought RSI"
            )
            logger.warning(
                "SKIPPING TRADE - Better to sit in cash than fight the trend"
            )
            raise ValueError(
                "No valid trading opportunities today. All symbols failed hard filters."
            )

        # Sort by score
        momentum_scores.sort(key=lambda x: x.score, reverse=True)

        # Log rankings
        logger.info("ETF Rankings:")
        for i, score in enumerate(momentum_scores, 1):
            logger.info(
                f"  {i}. {score.symbol}: {score.score:.2f} "
                f"(sentiment_boost: {score.sentiment_boost:.2f})"
            )

        best_etf = momentum_scores[0].symbol
        logger.info(
            f"Best ETF selected: {best_etf} with score {momentum_scores[0].score:.2f}"
        )

        return best_etf

    def should_rebalance(self) -> bool:
        """
        Determine if portfolio rebalancing is needed.

        Rebalancing is triggered when:
        1. It's been more than REBALANCE_FREQUENCY_DAYS since last rebalance
        2. Position concentration exceeds REBALANCE_THRESHOLD
        3. Holdings deviate significantly from target allocation

        Returns:
            True if rebalancing is recommended, False otherwise
        """
        # Check if enough time has passed
        if self.last_rebalance_date is None:
            if self.total_invested > 0:  # Have positions but never rebalanced
                logger.info("First rebalance check - considering rebalance")
                return True
            return False

        days_since_rebalance = (datetime.now() - self.last_rebalance_date).days

        if days_since_rebalance < self.REBALANCE_FREQUENCY_DAYS:
            logger.debug(
                f"Rebalance not needed - only {days_since_rebalance} days "
                f"since last rebalance (threshold: {self.REBALANCE_FREQUENCY_DAYS})"
            )
            return False

        # Check position concentration
        if not self.current_holdings:
            return False

        total_value = self._calculate_total_portfolio_value()
        if total_value == 0:
            return False

        # Calculate position percentages
        position_pcts = {
            symbol: (qty * self._get_current_price(symbol)) / total_value
            for symbol, qty in self.current_holdings.items()
        }

        # Check if any position is too concentrated
        max_concentration = max(position_pcts.values())
        target_allocation = 1.0 / len(self.etf_universe)  # Equal weight target

        deviation = abs(max_concentration - target_allocation)

        if deviation > self.REBALANCE_THRESHOLD:
            logger.info(
                f"Rebalance needed - position concentration {max_concentration:.1%} "
                f"deviates {deviation:.1%} from target {target_allocation:.1%}"
            )
            return True

        logger.info(
            f"Rebalance not needed - max deviation {deviation:.1%} "
            f"below threshold {self.REBALANCE_THRESHOLD:.1%}"
        )
        return False

    def rebalance_portfolio(self) -> List[TradeOrder]:
        """
        Rebalance portfolio to maintain target allocations.

        Process:
        1. Calculate current position values
        2. Determine target allocations (equal weight)
        3. Calculate required trades
        4. Execute rebalancing orders
        5. Update holdings and state

        Returns:
            List of trade orders executed during rebalancing

        Raises:
            ValueError: If rebalancing fails
        """
        logger.info("=" * 80)
        logger.info("Starting portfolio rebalancing")
        logger.info(f"Timestamp: {datetime.now().isoformat()}")

        rebalance_orders: List[TradeOrder] = []

        try:
            # Calculate current portfolio value
            total_value = self._calculate_total_portfolio_value()
            if total_value == 0:
                logger.warning("Portfolio value is zero - cannot rebalance")
                return []

            logger.info(f"Total portfolio value: ${total_value:.2f}")

            # Target allocation (equal weight across universe)
            target_allocation = 1.0 / len(self.etf_universe)
            target_value_per_etf = total_value * target_allocation

            logger.info(
                f"Target allocation per ETF: {target_allocation:.1%} (${target_value_per_etf:.2f})"
            )

            # Calculate current allocations
            current_allocations = {}
            for symbol in self.etf_universe:
                qty = self.current_holdings.get(symbol, 0.0)
                price = self._get_current_price(symbol)
                current_value = qty * price
                current_allocations[symbol] = {
                    "quantity": qty,
                    "price": price,
                    "value": current_value,
                    "pct": current_value / total_value,
                }

            # Log current state
            logger.info("Current allocations:")
            for symbol, alloc in current_allocations.items():
                logger.info(
                    f"  {symbol}: {alloc['pct']:.1%} (${alloc['value']:.2f}, "
                    f"{alloc['quantity']:.4f} shares @ ${alloc['price']:.2f})"
                )

            # Calculate required trades
            for symbol in self.etf_universe:
                current_value = current_allocations[symbol]["value"]
                target_value = target_value_per_etf
                value_diff = target_value - current_value

                # Only trade if difference is significant (> $1)
                if abs(value_diff) < 1.0:
                    continue

                price = current_allocations[symbol]["price"]
                quantity_diff = value_diff / price

                if value_diff > 0:
                    # Need to buy
                    order = self._create_buy_order(
                        symbol=symbol,
                        quantity=quantity_diff,
                        price=price,
                        sentiment=None,
                        reason=f"Rebalancing - target {target_allocation:.1%}",
                    )
                else:
                    # Need to sell
                    order = TradeOrder(
                        symbol=symbol,
                        action="sell",
                        quantity=abs(quantity_diff),
                        amount=abs(value_diff),
                        price=price,
                        order_type="market",
                        stop_loss=None,
                        timestamp=datetime.now(),
                        reason=f"Rebalancing - target {target_allocation:.1%}",
                    )

                rebalance_orders.append(order)
                logger.info(
                    f"Rebalance order: {order.action.upper()} {order.quantity:.4f} "
                    f"{order.symbol} @ ${order.price:.2f} (${order.amount:.2f})"
                )

            # Execute orders via Alpaca
            if self.alpaca_trader:
                for order in rebalance_orders:
                    try:
                        if order.action == "buy":
                            executed = self.alpaca_trader.execute_order(
                                symbol=order.symbol, amount_usd=order.amount, side="buy"
                            )
                            logger.info(f"Rebalance buy executed: {executed['id']}")
                        else:  # sell
                            # Sell fractional shares by dollar amount
                            executed = self.alpaca_trader.execute_order(
                                symbol=order.symbol,
                                amount_usd=order.amount,
                                side="sell",
                            )
                            logger.info(f"Rebalance sell executed: {executed['id']}")
                    except Exception as e:
                        logger.error(
                            f"Failed to execute rebalance order for {order.symbol}: {e}"
                        )
                        continue

            # Update state
            for order in rebalance_orders:
                if order.action == "buy":
                    self.current_holdings[order.symbol] = (
                        self.current_holdings.get(order.symbol, 0.0) + order.quantity
                    )
                else:  # sell
                    self.current_holdings[order.symbol] = (
                        self.current_holdings.get(order.symbol, 0.0) - order.quantity
                    )

            self.last_rebalance_date = datetime.now()
            self.trades_executed.extend(rebalance_orders)

            logger.info(
                f"Rebalancing complete - executed {len(rebalance_orders)} orders"
            )
            logger.info("=" * 80)

            return rebalance_orders

        except Exception as e:
            logger.error(f"Error during rebalancing: {str(e)}", exc_info=True)
            raise ValueError(f"Rebalancing failed: {str(e)}") from e

    def get_account_summary(self) -> Dict[str, any]:
        """
        Get comprehensive account summary from Alpaca.

        Returns:
            Dictionary containing account information and portfolio data
        """
        if not self.alpaca_trader:
            logger.warning("Alpaca trader not initialized")
            return {
                "account_value": self._calculate_total_portfolio_value(),
                "buying_power": 0.0,
                "cash": 0.0,
                "portfolio_value": self._calculate_total_portfolio_value(),
                "positions": [],
                "source": "local_tracking",
            }

        try:
            # Get account info
            account_info = self.alpaca_trader.get_account_info()

            # Get positions
            positions = self.alpaca_trader.get_positions()

            # Get portfolio performance
            performance = self.alpaca_trader.get_portfolio_performance()

            summary = {
                "account_value": account_info["portfolio_value"],
                "buying_power": account_info["buying_power"],
                "cash": account_info["cash"],
                "equity": account_info["equity"],
                "portfolio_value": performance["portfolio_value"],
                "profit_loss": performance["profit_loss"],
                "profit_loss_pct": performance["profit_loss_pct"],
                "positions": positions,
                "positions_count": len(positions),
                "source": "alpaca_api",
                "timestamp": datetime.now().isoformat(),
            }

            logger.info(f"Account summary retrieved: ${summary['account_value']:.2f}")
            return summary

        except Exception as e:
            logger.error(f"Error getting account summary: {e}")
            return {
                "account_value": self._calculate_total_portfolio_value(),
                "buying_power": 0.0,
                "cash": 0.0,
                "portfolio_value": self._calculate_total_portfolio_value(),
                "positions": [],
                "source": "error_fallback",
                "error": str(e),
            }

    def update_daily_performance(self) -> None:
        """
        Update daily performance metrics and returns.

        Should be called at end of each trading day to track performance.
        """
        try:
            # Calculate today's portfolio value
            current_value = self._calculate_total_portfolio_value()

            # Calculate daily return if we have previous value
            if self.total_value > 0:
                daily_return = (current_value - self.total_value) / self.total_value
                self.daily_returns.append(daily_return)
                logger.info(f"Daily return: {daily_return*100:.2f}%")

            # Update stored value
            self.total_value = current_value

            # Record with risk manager if available
            if self.risk_manager and len(self.daily_returns) > 0:
                pnl = current_value - self.total_invested
                self.risk_manager.record_trade_result(pnl)

        except Exception as e:
            logger.error(f"Error updating daily performance: {e}")

    def get_performance_metrics(self) -> Dict[str, any]:
        """
        Calculate comprehensive performance metrics for the strategy.

        Returns:
            Dictionary containing:
            - total_invested: Total capital deployed
            - current_value: Current portfolio value
            - total_return: Absolute return in dollars
            - total_return_pct: Percentage return
            - annualized_return: Annualized return percentage
            - sharpe_ratio: Risk-adjusted return metric
            - max_drawdown: Maximum peak-to-trough decline
            - win_rate: Percentage of profitable days
            - num_trades: Total number of trades executed
            - average_trade_size: Average trade amount
            - holding_period_days: Days since first trade
            - daily_returns: List of daily returns
        """
        logger.info("Calculating performance metrics")

        # Calculate current portfolio value
        current_value = self._calculate_total_portfolio_value()

        # Basic metrics
        total_return = current_value - self.total_invested
        total_return_pct = (
            (total_return / self.total_invested * 100)
            if self.total_invested > 0
            else 0.0
        )

        # Calculate holding period
        if self.trades_executed:
            first_trade_date = min(trade.timestamp for trade in self.trades_executed)
            holding_period_days = (datetime.now() - first_trade_date).days
        else:
            holding_period_days = 0

        # Annualized return
        if holding_period_days > 0 and self.total_invested > 0:
            years = holding_period_days / 365.25
            annualized_return = (
                (pow(current_value / self.total_invested, 1 / years) - 1) * 100
                if years > 0
                else 0.0
            )
        else:
            annualized_return = 0.0

        # Calculate Sharpe ratio
        if len(self.daily_returns) > 1:
            mean_return = np.mean(self.daily_returns)
            std_return = np.std(self.daily_returns)
            risk_free_rate_daily = 0.04 / 252  # 4% annual / 252 trading days
            sharpe_ratio = (
                (mean_return - risk_free_rate_daily) / std_return * np.sqrt(252)
                if std_return > 0
                else 0.0
            )
        else:
            sharpe_ratio = 0.0

        # Calculate max drawdown
        max_drawdown = self._calculate_max_drawdown()

        # Win rate
        positive_days = sum(1 for r in self.daily_returns if r > 0)
        win_rate = (
            (positive_days / len(self.daily_returns) * 100)
            if self.daily_returns
            else 0.0
        )

        # Trade statistics
        num_trades = len(self.trades_executed)
        average_trade_size = (
            sum(trade.amount for trade in self.trades_executed) / num_trades
            if num_trades > 0
            else 0.0
        )

        metrics = {
            "total_invested": self.total_invested,
            "current_value": current_value,
            "total_return": total_return,
            "total_return_pct": total_return_pct,
            "annualized_return": annualized_return,
            "sharpe_ratio": sharpe_ratio,
            "max_drawdown": max_drawdown,
            "win_rate": win_rate,
            "num_trades": num_trades,
            "average_trade_size": average_trade_size,
            "holding_period_days": holding_period_days,
            "current_holdings": self.current_holdings.copy(),
            "last_rebalance_date": self.last_rebalance_date,
        }

        # Log summary
        logger.info("Performance Summary:")
        logger.info(f"  Total Invested: ${metrics['total_invested']:.2f}")
        logger.info(f"  Current Value: ${metrics['current_value']:.2f}")
        logger.info(
            f"  Total Return: ${metrics['total_return']:.2f} ({metrics['total_return_pct']:.2f}%)"
        )
        logger.info(f"  Annualized Return: {metrics['annualized_return']:.2f}%")
        logger.info(f"  Sharpe Ratio: {metrics['sharpe_ratio']:.2f}")
        logger.info(f"  Max Drawdown: {metrics['max_drawdown']:.2f}%")
        logger.info(f"  Win Rate: {metrics['win_rate']:.1f}%")
        logger.info(f"  Number of Trades: {metrics['num_trades']}")
        logger.info(f"  Holding Period: {metrics['holding_period_days']} days")

        return metrics

    # ==================== Private Helper Methods ====================

    def _get_market_sentiment(self) -> MarketSentiment:
        """
        Query sentiment data (Reddit + News) for current market sentiment.

        This method now uses the sentiment_loader to get pre-collected sentiment
        from Reddit and news sources instead of querying LLMs in real-time.

        Priority:
        1. Load pre-collected sentiment from data/sentiment/
        2. Use SPY as proxy for overall market sentiment
        3. Apply risk-off filter if market is bearish

        Returns:
            MarketSentiment enum value
        """
        if not self.use_sentiment:
            logger.debug("Sentiment disabled - using default neutral")
            return MarketSentiment.NEUTRAL

        try:
            # Load latest sentiment data
            sentiment_data = load_latest_sentiment()

            # Check if data is available
            if not sentiment_data.get("sentiment_by_ticker"):
                logger.warning("No sentiment data available - using neutral")
                return MarketSentiment.NEUTRAL

            # Get market regime from SPY sentiment
            market_regime = get_market_regime(sentiment_data)

            # Get SPY sentiment score
            spy_score, spy_confidence, _ = get_ticker_sentiment("SPY", sentiment_data)

            # Convert 0-100 sentiment score to MarketSentiment enum
            # 0-30 = very bearish, 30-40 = bearish, 40-60 = neutral,
            # 60-70 = bullish, 70-100 = very bullish
            if spy_score < 30:
                sentiment = MarketSentiment.VERY_BEARISH
            elif spy_score < 40:
                sentiment = MarketSentiment.BEARISH
            elif spy_score < 60:
                sentiment = MarketSentiment.NEUTRAL
            elif spy_score < 70:
                sentiment = MarketSentiment.BULLISH
            else:
                sentiment = MarketSentiment.VERY_BULLISH

            # Optionally log historical context from RAG store
            if getattr(self, "sentiment_rag_enabled", True):
                history = get_sentiment_history("SPY", limit=5)
                if history:
                    logger.info("Recent SPY sentiment snapshots (RAG):")
                    for entry in history:
                        meta = entry["metadata"]
                        logger.info(
                            "  %s score=%.1f confidence=%s regime=%s",
                            meta.get("snapshot_date"),
                            meta.get("sentiment_score", 0.0),
                            meta.get("confidence", "n/a"),
                            meta.get("market_regime", "n/a"),
                        )

            logger.info(
                f"Sentiment analysis: {sentiment.value} "
                f"(SPY score: {spy_score:.1f}, confidence: {spy_confidence}, "
                f"market regime: {market_regime})"
            )

            # Log data freshness
            meta = sentiment_data.get("meta", {})
            freshness = meta.get("freshness", "unknown")
            days_old = meta.get("days_old", 0)
            logger.info(
                f"Sentiment data: {freshness} ({days_old} days old), "
                f"sources: {', '.join(meta.get('sources', []))}"
            )

            return sentiment

        except Exception as e:
            logger.error(f"Error loading sentiment data: {e}")
            logger.debug("Falling back to neutral sentiment")
            return MarketSentiment.NEUTRAL

    def _calculate_all_momentum_scores(
        self, sentiment: MarketSentiment
    ) -> List[MomentumScore]:
        """
        Calculate momentum scores for all ETFs in universe.

        Args:
            sentiment: Current market sentiment for boosting

        Returns:
            List of MomentumScore objects
        """
        scores = []
        sentiment_boost = self._get_sentiment_boost(sentiment)

        for symbol in self.etf_universe:
            try:
                base_score = self.calculate_momentum(symbol)

                # Skip if symbol was rejected by hard filters (score = -1)
                if base_score < 0:
                    logger.info(f"{symbol} skipped - failed hard filters")
                    continue

                # Apply sentiment boost
                adjusted_score = base_score + sentiment_boost
                adjusted_score = max(0, min(100, adjusted_score))

                # Get additional metrics for the score object
                ticker = yf.Ticker(symbol)
                hist = ticker.history(period="6mo")

                returns_1m = self._calculate_period_return(hist, 21)
                returns_3m = self._calculate_period_return(hist, 63)
                returns_6m = self._calculate_period_return(hist, 126)

                daily_returns = hist["Close"].pct_change().dropna()
                volatility = daily_returns.std() * np.sqrt(252)

                risk_free_rate = 0.04
                excess_return = returns_6m - risk_free_rate
                sharpe_ratio = excess_return / volatility if volatility > 0 else 0

                rsi = self._calculate_rsi(hist["Close"], self.RSI_PERIOD)

                # Calculate MACD and volume
                macd_value, macd_signal, macd_histogram = self._calculate_macd(hist["Close"])
                volume_ratio = self._calculate_volume_ratio(hist)

                score_obj = MomentumScore(
                    symbol=symbol,
                    score=adjusted_score,
                    returns_1m=returns_1m,
                    returns_3m=returns_3m,
                    returns_6m=returns_6m,
                    volatility=volatility,
                    sharpe_ratio=sharpe_ratio,
                    rsi=rsi,
                    macd_value=macd_value,
                    macd_signal=macd_signal,
                    macd_histogram=macd_histogram,
                    volume_ratio=volume_ratio,
                    sentiment_boost=sentiment_boost,
                    timestamp=datetime.now(),
                )

                scores.append(score_obj)
                self.momentum_history.append(score_obj)

            except Exception as e:
                logger.error(f"Failed to calculate momentum for {symbol}: {str(e)}")
                continue

        return scores

    def _get_sentiment_boost(self, sentiment: MarketSentiment) -> float:
        """
        Convert sentiment to momentum score adjustment.

        Args:
            sentiment: Market sentiment

        Returns:
            Score boost (positive or negative)
        """
        sentiment_map = {
            MarketSentiment.VERY_BULLISH: 10.0,
            MarketSentiment.BULLISH: 5.0,
            MarketSentiment.NEUTRAL: 0.0,
            MarketSentiment.BEARISH: -5.0,
            MarketSentiment.VERY_BEARISH: -10.0,
        }
        return sentiment_map.get(sentiment, 0.0)

    def _get_current_price(self, symbol: str) -> Optional[float]:
        """
        Get current market price for symbol.

        Args:
            symbol: Ticker symbol

        Returns:
            Current price or None if unavailable
        """
        try:
            ticker = yf.Ticker(symbol)
            data = ticker.history(period="1d")
            if not data.empty:
                return float(data["Close"].iloc[-1])
            return None
        except Exception as e:
            logger.error(f"Error fetching price for {symbol}: {str(e)}")
            return None

    def _calculate_period_return(self, hist: pd.DataFrame, periods: int) -> float:
        """
        Calculate return over specified number of periods.

        Args:
            hist: Historical price DataFrame
            periods: Number of periods to look back

        Returns:
            Period return as decimal (e.g., 0.05 for 5%)
        """
        if len(hist) < periods:
            periods = len(hist) - 1

        if periods <= 0:
            return 0.0

        end_price = hist["Close"].iloc[-1]
        start_price = hist["Close"].iloc[-periods]

        return (end_price - start_price) / start_price

    def _calculate_rsi(self, prices: pd.Series, period: int = 14) -> float:
        """
        Calculate Relative Strength Index (RSI).

        Args:
            prices: Price series
            period: RSI period (default: 14)

        Returns:
            RSI value (0-100)
        """
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()

        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))

        return float(rsi.iloc[-1]) if not pd.isna(rsi.iloc[-1]) else 50.0

    def _calculate_macd(
        self, prices: pd.Series
    ) -> Tuple[float, float, float]:
        """
        Calculate MACD (Moving Average Convergence Divergence).

        Uses shared utility from src.utils.technical_indicators.

        Args:
            prices: Price series

        Returns:
            Tuple of (macd_value, signal_line, histogram)
        """
        from src.utils.technical_indicators import calculate_macd
        
        return calculate_macd(
            prices,
            fast_period=self.MACD_FAST_PERIOD,
            slow_period=self.MACD_SLOW_PERIOD,
            signal_period=self.MACD_SIGNAL_PERIOD,
        )

    def _calculate_volume_ratio(self, hist: pd.DataFrame) -> float:
        """
        Calculate volume ratio (current vs 20-day average).

        Uses shared utility from src.utils.technical_indicators.

        Args:
            hist: Historical price DataFrame

        Returns:
            Volume ratio (current / 20-day average)
        """
        from src.utils.technical_indicators import calculate_volume_ratio
        
        return calculate_volume_ratio(hist, window=20)

    def _validate_trade(
        self, symbol: str, quantity: float, price: float, sentiment: MarketSentiment
    ) -> bool:
        """
        Validate trade against risk management rules using RiskManager.

        Args:
            symbol: Ticker symbol
            quantity: Number of shares
            price: Price per share
            sentiment: Current market sentiment

        Returns:
            True if trade passes validation, False otherwise
        """
        trade_value = quantity * price

        # Basic validation - trade value
        if trade_value > self.daily_allocation * 1.1:  # 10% tolerance
            logger.warning(f"Trade value ${trade_value:.2f} exceeds daily allocation")
            return False
        
        # CTO Decision: Position size limit - max 50% per symbol
        # Prevents concentration like SPY (74% of portfolio)
        total_portfolio_value = self._calculate_total_portfolio_value()
        if total_portfolio_value > 0:
            current_position_value = self.current_holdings.get(symbol, 0) * price
            new_position_value = current_position_value + trade_value
            position_pct = (new_position_value / (total_portfolio_value + trade_value)) * 100
            
            if position_pct > 50:
                logger.warning(
                    f"Position size limit exceeded: {symbol} would be {position_pct:.1f}% of portfolio "
                    f"(max 50%). Skipping trade to maintain diversification."
                )
                return False

        # Use RiskManager if available
        if self.risk_manager:
            try:
                # Get account info
                account_value = (
                    self._calculate_total_portfolio_value() + self.total_invested
                )
                if account_value == 0:
                    account_value = 10000.0  # Default starting value

                # Convert sentiment to score
                sentiment_score = self._get_sentiment_boost(sentiment) / 10.0

                # Validate with risk manager
                validation = self.risk_manager.validate_trade(
                    symbol=symbol,
                    amount=trade_value,
                    sentiment_score=sentiment_score,
                    account_value=account_value,
                    trade_type="BUY",
                )

                if not validation["valid"]:
                    logger.warning(
                        f"Risk manager rejected trade: {validation['reason']}"
                    )
                    return False

                if validation["warnings"]:
                    for warning in validation["warnings"]:
                        logger.warning(f"Risk manager warning: {warning}")

                # Check if trading is allowed (circuit breakers)
                if not self.risk_manager.can_trade(
                    account_value, self.risk_manager.metrics.daily_pl
                ):
                    logger.warning("Trading suspended by circuit breaker")
                    return False

                if self.langchain_guard_enabled and not self._langchain_guard(
                    symbol, sentiment
                ):
                    logger.warning(
                        "LangChain approval gate rejected trade for %s", symbol
                    )
                    return False

                return True

            except Exception as e:
                logger.error(f"Error in risk validation: {e}")
                # Fall through to basic validation

        if self.langchain_guard_enabled and not self._langchain_guard(symbol, sentiment):
            logger.warning("LangChain approval gate rejected trade for %s", symbol)
            return False

        return True

    def _create_buy_order(
        self,
        symbol: str,
        quantity: float,
        price: float,
        sentiment: Optional[MarketSentiment],
        reason: Optional[str] = None,
    ) -> TradeOrder:
        """
        Create a buy order with stop-loss.

        Args:
            symbol: Ticker symbol
            quantity: Number of shares
            price: Price per share
            sentiment: Current market sentiment
            reason: Trade reason (optional)

        Returns:
            TradeOrder object
        """
        amount = quantity * price
        stop_loss_price = price * (1 - self.stop_loss_pct)

        if reason is None:
            reason = f"Daily DCA purchase - {sentiment.value if sentiment else 'neutral'} sentiment"

        return TradeOrder(
            symbol=symbol,
            action="buy",
            quantity=quantity,
            amount=amount,
            price=price,
            order_type="market",
            stop_loss=stop_loss_price,
            timestamp=datetime.now(),
            reason=reason,
        )

    def _langchain_guard(self, symbol: str, sentiment: MarketSentiment) -> bool:
        """
        Invoke the LangChain approval agent if enabled.

        Returns True when the agent responds with APPROVE. On failure, defaults to
        fail-open unless LANGCHAIN_APPROVAL_FAIL_OPEN is set to false.
        """
        try:
            if self._langchain_agent is None:
                from langchain_agents.agents import build_price_action_agent

                self._langchain_agent = build_price_action_agent()

            prompt = (
                "You are the trading desk's approval co-pilot. Evaluate whether "
                "we should execute a BUY trade today. Respond with a single word: "
                "'APPROVE' or 'DECLINE'.\n\n"
                f"Ticker: {symbol}\n"
                f"Current market sentiment: {sentiment.value}\n"
                "Use the available sentiment tools to gather recent context. "
                "Decline if the data is missing, highly bearish, or confidence is low."
            )

            response = self._langchain_agent.invoke({"input": prompt})
            if isinstance(response, dict):
                text = response.get("output", "")
            else:
                text = str(response)

            normalized = text.strip().lower()
            approved = "approve" in normalized and "decline" not in normalized

            if approved:
                logger.info("LangChain approval granted for %s: %s", symbol, text)
            else:
                logger.warning("LangChain approval denied for %s: %s", symbol, text)

            return approved
        except Exception as exc:
            logger.error("LangChain approval gate error: %s", exc)
            fail_open = os.getenv("LANGCHAIN_APPROVAL_FAIL_OPEN", "true").lower()
            if fail_open == "true":
                logger.warning(
                    "LangChain approval unavailable; defaulting to APPROVE (fail-open)."
                )
                return True
            return False

    def _update_holdings(self, symbol: str, quantity: float) -> None:
        """
        Update current holdings after trade.

        Args:
            symbol: Ticker symbol
            quantity: Quantity to add (positive) or remove (negative)
        """
        self.current_holdings[symbol] = (
            self.current_holdings.get(symbol, 0.0) + quantity
        )

        # Remove if quantity is now zero or negative
        if self.current_holdings[symbol] <= 0:
            self.current_holdings.pop(symbol, None)

    def _calculate_total_portfolio_value(self) -> float:
        """
        Calculate total current value of all holdings.

        Returns:
            Total portfolio value in dollars
        """
        total = 0.0
        for symbol, quantity in self.current_holdings.items():
            price = self._get_current_price(symbol)
            if price:
                total += quantity * price
        return total

    def _calculate_max_drawdown(self) -> float:
        """
        Calculate maximum drawdown from peak.

        Returns:
            Maximum drawdown as percentage
        """
        if not self.daily_returns:
            return 0.0

        # Calculate cumulative returns
        cumulative = np.cumprod(1 + np.array(self.daily_returns))
        running_max = np.maximum.accumulate(cumulative)
        drawdown = (cumulative - running_max) / running_max

        return float(abs(np.min(drawdown)) * 100) if len(drawdown) > 0 else 0.0


# Example usage
if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    # Initialize strategy
    strategy = CoreStrategy(
        daily_allocation=6.0, etf_universe=["SPY", "QQQ", "VOO"], stop_loss_pct=0.05
    )

    # Execute daily routine
    order = strategy.execute_daily()

    if order:
        print(
            f"\nOrder executed: {order.action.upper()} {order.quantity:.4f} "
            f"{order.symbol} @ ${order.price:.2f}"
        )

    # Get performance metrics
    metrics = strategy.get_performance_metrics()
    print(f"\nCurrent Portfolio Value: ${metrics['current_value']:.2f}")
    print(
        f"Total Return: ${metrics['total_return']:.2f} ({metrics['total_return_pct']:.2f}%)"
    )
