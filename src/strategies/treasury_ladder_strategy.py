"""
Treasury Ladder Strategy

Implements a 3-tier treasury ETF ladder with dynamic allocation based on yield curve analysis.
Provides stable income while adapting to interest rate environment and yield curve inversions.

Strategy Overview:
- Base Allocation: SHY (40%), IEF (40%), TLT (20%)
- Yield Curve Detection: Shifts to SHY when 2yr > 10yr (inversion)
- Automatic Rebalancing: Triggers when allocation drifts >5%
- Risk Management: Low-risk, government-backed securities

Treasury ETFs:
- SHY: iShares 1-3 Year Treasury Bond ETF (short-term, low duration)
- IEF: iShares 7-10 Year Treasury Bond ETF (intermediate duration)
- TLT: iShares 20+ Year Treasury Bond ETF (long-term, high duration)

Yield Curve Strategies:
- Normal Curve (2yr < 10yr): Balanced ladder (40/40/20)
- Flat Curve (2yr ≈ 10yr): Slight shift to short (50/35/15)
- Inverted Curve (2yr > 10yr): Heavy short (70/25/5) - recession hedge

Integration:
- Uses FRED API for real-time yield data (DGS2, DGS10)
- Integrates with AlpacaTrader for execution
- Daily rebalancing checks with 5% drift threshold

Research Context (Dec 2025):
- Current yields: 2-year ~4.17%, 10-year ~4.19%, 30-year ~4.36%
- Fed expected to cut rates, but long-term settling around 3-4%
- Treasury ladder provides stability and income in volatile markets

Author: Trading System
Created: 2025-12-02
"""

import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Optional

from src.core.alpaca_trader import AlpacaTrader
from src.rag.collectors.fred_collector import FREDCollector

# Configure logging
logger = logging.getLogger(__name__)


class YieldCurveRegime(Enum):
    """Yield curve regime classification."""

    NORMAL = "normal"  # 2yr < 10yr (typical)
    FLAT = "flat"  # 2yr ≈ 10yr (transition)
    INVERTED = "inverted"  # 2yr > 10yr (recession signal)
    STEEP = "steep"  # 2s10s very low - steepener opportunity


class RateVolatilityRegime(Enum):
    """Rate volatility regime based on MOVE Index."""

    LOW = "low"  # MOVE < 70 - safe to extend duration
    NORMAL = "normal"  # 70 <= MOVE <= 120 - standard allocation
    HIGH = "high"  # MOVE > 120 - reduce duration exposure


@dataclass
class TreasuryAllocation:
    """Treasury ladder allocation details."""

    shy_pct: float  # Short-term (1-3yr)
    ief_pct: float  # Intermediate (7-10yr)
    tlt_pct: float  # Long-term (20+yr)
    regime: YieldCurveRegime
    spread: float  # 10yr - 2yr spread
    rationale: str
    timestamp: datetime
    # Dynamic long ETF selection (TLT vs ZROZ)
    long_etf: str = "TLT"  # Default to TLT, switch to ZROZ when 10Y < 4.05%
    # GOVT core allocation (fixed 25%)
    govt_pct: float = 0.25  # Fixed intermediate treasury allocation
    # Steepener override
    steepener_active: bool = False  # True when 2s10s < 0.2%
    steepener_extra_pct: float = 0.0  # Extra allocation to long treasuries


@dataclass
class RebalanceDecision:
    """Rebalancing decision details."""

    should_rebalance: bool
    current_allocation: dict[str, float]
    target_allocation: dict[str, float]
    drift_pct: dict[str, float]
    max_drift: float
    reason: str
    timestamp: datetime


class TreasuryLadderStrategy:
    """
    Treasury Ladder Strategy with dynamic allocation based on yield curve.

    This strategy implements a 3-tier treasury ETF ladder (SHY, IEF, TLT) with
    intelligent rebalancing based on yield curve conditions. It provides stable
    income and capital preservation while adapting to interest rate environments.

    Key Features:
    - 3-tier ladder: Short (SHY), Intermediate (IEF), Long (TLT)
    - Yield curve inversion detection via FRED API
    - Dynamic allocation shifts based on yield curve shape
    - Automatic rebalancing when drift exceeds 5%
    - Low-risk government-backed securities
    - Integration with Alpaca for fractional share trading

    Attributes:
        daily_allocation (float): Daily dollar amount to invest
        rebalance_threshold (float): Drift percentage that triggers rebalance
        etf_symbols (List[str]): Treasury ETF symbols [SHY, IEF, TLT]
        current_holdings (Dict[str, float]): Current position values by symbol
        last_rebalance_date (Optional[datetime]): Last rebalancing timestamp
        alpaca_trader (AlpacaTrader): Alpaca API client
        fred_collector (FREDCollector): FRED API client for yield data
    """

    # Treasury ETF universe
    ETF_SYMBOLS = ["SHY", "IEF", "TLT", "ZROZ", "GOVT", "BIL"]

    # Fixed core allocation - intermediate treasury for stable carry
    GOVT_CORE_ALLOCATION = 0.25  # 25% fixed GOVT allocation

    # Base allocations for different yield curve regimes
    # Normal curve: balanced ladder
    ALLOCATION_NORMAL = {"SHY": 0.40, "IEF": 0.40, "TLT": 0.20}

    # Flat curve: slight preference for short duration
    ALLOCATION_FLAT = {"SHY": 0.50, "IEF": 0.35, "TLT": 0.15}

    # Inverted curve: heavy preference for short duration (recession hedge)
    ALLOCATION_INVERTED = {"SHY": 0.70, "IEF": 0.25, "TLT": 0.05}

    # Yield curve regime thresholds (percentage points)
    SPREAD_INVERTED_THRESHOLD = 0.0  # Spread < 0 = inverted
    SPREAD_FLAT_THRESHOLD = 0.5  # Spread < 50bps = flat
    SPREAD_STEEPENER_THRESHOLD = 0.2  # Spread < 20bps = steepener opportunity

    # Dynamic long ETF selection thresholds
    YIELD_10Y_ZROZ_THRESHOLD = 4.05  # Switch to ZROZ when 10Y < 4.05%

    # Steepener override parameters
    STEEPENER_EXTRA_ALLOCATION = 0.15  # Add 15% extra to long treasuries when triggered

    # MOVE Index thresholds for rate volatility
    MOVE_LOW_VOL_THRESHOLD = 70  # MOVE < 70 = quiet rates
    MOVE_HIGH_VOL_THRESHOLD = 120  # MOVE > 120 = volatile rates

    # Duration multipliers based on MOVE
    MOVE_DURATION_ADJUSTMENTS = {
        "low": 1.3,  # Increase duration by 30% when rates quiet
        "normal": 1.0,  # Standard allocation
        "high": 0.5,  # Reduce duration by 50% when rates volatile
    }

    # Rebalancing parameters
    DEFAULT_REBALANCE_THRESHOLD = 0.05  # 5% drift triggers rebalance
    MIN_REBALANCE_INTERVAL_DAYS = 7  # Minimum days between rebalances

    def __init__(
        self,
        daily_allocation: float = 10.0,
        rebalance_threshold: float = DEFAULT_REBALANCE_THRESHOLD,
        paper: bool = True,
    ):
        """
        Initialize the Treasury Ladder Strategy.

        Args:
            daily_allocation: Daily dollar amount to invest (default: $10)
            rebalance_threshold: Drift percentage that triggers rebalance (default: 5%)
            paper: Whether to use paper trading (default: True)

        Raises:
            ValueError: If daily_allocation is non-positive or threshold invalid
        """
        if daily_allocation <= 0:
            raise ValueError(f"daily_allocation must be positive, got {daily_allocation}")

        if not 0 < rebalance_threshold < 1:
            raise ValueError(
                f"rebalance_threshold must be between 0 and 1, got {rebalance_threshold}"
            )

        self.daily_allocation = daily_allocation
        self.rebalance_threshold = rebalance_threshold
        self.etf_symbols = self.ETF_SYMBOLS.copy()

        # Strategy state
        self.current_holdings: dict[str, float] = {}
        self.last_rebalance_date: Optional[datetime] = None
        self.current_regime: Optional[YieldCurveRegime] = None

        # Performance tracking
        self.total_invested: float = 0.0
        self.total_value: float = 0.0
        self.rebalance_history: list[RebalanceDecision] = []

        # Initialize dependencies
        try:
            self.alpaca_trader = AlpacaTrader(paper=paper)
            logger.info("Successfully initialized Alpaca trader")
        except Exception as e:
            logger.error(f"Failed to initialize Alpaca trader: {e}")
            self.alpaca_trader = None

        try:
            self.fred_collector = FREDCollector()
            logger.info("Successfully initialized FRED collector")
        except Exception as e:
            logger.warning(f"Failed to initialize FRED collector: {e}")
            self.fred_collector = None

        logger.info(
            f"TreasuryLadderStrategy initialized: "
            f"daily_allocation=${daily_allocation:.2f}, "
            f"rebalance_threshold={rebalance_threshold * 100:.1f}%, "
            f"etfs={self.etf_symbols}"
        )

    def analyze_yield_curve(self) -> tuple[YieldCurveRegime, float, str]:
        """
        Analyze the current yield curve using FRED data.

        Fetches 2-year and 10-year treasury yields from FRED API and determines
        the yield curve regime (normal, flat, or inverted).

        Returns:
            Tuple of (regime, spread, rationale):
                - regime: YieldCurveRegime enum value
                - spread: 10yr - 2yr spread in percentage points
                - rationale: Human-readable explanation

        Raises:
            Exception: If yield data cannot be fetched
        """
        logger.info("Analyzing yield curve...")

        if not self.fred_collector:
            logger.warning("FRED collector not available, assuming normal curve")
            return YieldCurveRegime.NORMAL, 0.50, "FRED API unavailable, using default"

        try:
            # Fetch 2-year and 10-year treasury yields
            end_date = datetime.now()
            start_date = end_date - timedelta(days=7)

            dgs2_data = self.fred_collector._fetch_series(
                "DGS2",
                start_date.strftime("%Y-%m-%d"),
                end_date.strftime("%Y-%m-%d"),
            )

            dgs10_data = self.fred_collector._fetch_series(
                "DGS10",
                start_date.strftime("%Y-%m-%d"),
                end_date.strftime("%Y-%m-%d"),
            )

            # Also try to get the spread directly
            spread_data = self.fred_collector._fetch_series(
                "T10Y2Y",
                start_date.strftime("%Y-%m-%d"),
                end_date.strftime("%Y-%m-%d"),
            )

            # Use direct spread if available, otherwise calculate
            if spread_data and spread_data.get("latest_value") != ".":
                spread = float(spread_data["latest_value"])
                logger.info(f"Yield curve spread (10yr-2yr): {spread:.2f}%")
            elif dgs2_data and dgs10_data:
                # Calculate spread manually
                yield_2yr = float(dgs2_data.get("latest_value", 0))
                yield_10yr = float(dgs10_data.get("latest_value", 0))
                spread = yield_10yr - yield_2yr
                logger.info(
                    f"Calculated spread: 10yr={yield_10yr:.2f}%, 2yr={yield_2yr:.2f}%, spread={spread:.2f}%"
                )
            else:
                logger.warning("Could not fetch yield data, using default normal curve")
                return (
                    YieldCurveRegime.NORMAL,
                    0.50,
                    "Yield data unavailable, using default",
                )

            # Determine regime based on spread
            if spread < self.SPREAD_INVERTED_THRESHOLD:
                regime = YieldCurveRegime.INVERTED
                rationale = (
                    f"INVERTED: 2yr yield exceeds 10yr by {abs(spread):.2f}%. "
                    "Historical recession indicator. Shifting to short duration."
                )
            elif spread < self.SPREAD_FLAT_THRESHOLD:
                regime = YieldCurveRegime.FLAT
                rationale = (
                    f"FLAT: Spread only {spread:.2f}%. Late cycle indicator. "
                    "Moderately favoring short duration."
                )
            else:
                regime = YieldCurveRegime.NORMAL
                rationale = (
                    f"NORMAL: Healthy {spread:.2f}% spread. "
                    "Balanced allocation across duration ladder."
                )

            logger.info(f"Yield curve regime: {regime.value} - {rationale}")
            self.current_regime = regime

            return regime, spread, rationale

        except Exception as e:
            logger.error(f"Failed to analyze yield curve: {e}")
            # Default to normal curve on error
            return (
                YieldCurveRegime.NORMAL,
                0.50,
                f"Error fetching yields: {e}, using default",
            )

    def get_10y_yield(self) -> float:
        """
        Fetch current 10-year Treasury yield from FRED.

        Returns:
            float: Current 10Y yield in percentage (e.g., 4.19 for 4.19%)
        """
        if not self.fred_collector:
            logger.warning("FRED collector unavailable, using default 10Y yield of 4.20%")
            return 4.20

        try:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=7)

            dgs10_data = self.fred_collector._fetch_series(
                "DGS10",
                start_date.strftime("%Y-%m-%d"),
                end_date.strftime("%Y-%m-%d"),
            )

            if dgs10_data and dgs10_data.get("latest_value") != ".":
                yield_10y = float(dgs10_data["latest_value"])
                logger.info(f"Current 10Y Treasury yield: {yield_10y:.2f}%")
                return yield_10y
            else:
                logger.warning("10Y yield data unavailable, using default 4.20%")
                return 4.20

        except Exception as e:
            logger.error(f"Failed to fetch 10Y yield: {e}")
            return 4.20

    def select_long_etf(self, yield_10y: float) -> str:
        """
        Dynamically select long-duration ETF based on 10Y yield level.

        When 10Y yield is low (< 4.05%), use ZROZ (ultra-long 25+ year zero coupon)
        for 2-3% extra yield with slightly higher duration risk.

        When 10Y yield is higher (>= 4.05%), stick with TLT (20+ year) for
        more moderate duration exposure.

        Args:
            yield_10y: Current 10-year Treasury yield in percentage

        Returns:
            str: "ZROZ" or "TLT" ticker symbol
        """
        if yield_10y < self.YIELD_10Y_ZROZ_THRESHOLD:
            logger.info(
                f"10Y yield ({yield_10y:.2f}%) < {self.YIELD_10Y_ZROZ_THRESHOLD}% → "
                "Selecting ZROZ (ultra-long) for extra carry"
            )
            return "ZROZ"
        else:
            logger.info(
                f"10Y yield ({yield_10y:.2f}%) >= {self.YIELD_10Y_ZROZ_THRESHOLD}% → "
                "Selecting TLT (standard long duration)"
            )
            return "TLT"

    def check_steepener_signal(self, spread: float) -> tuple[bool, float]:
        """
        Check if steepener trade should be activated.

        The 2s/10s steepener is one of the best mean-reverting Treasury trades.
        When the spread is extremely flat (< 0.2%), historical data shows
        high probability of curve steepening, making long duration attractive.

        Args:
            spread: Current 10Y-2Y spread in percentage points

        Returns:
            tuple: (should_activate, extra_allocation_pct)
        """
        if spread < self.SPREAD_STEEPENER_THRESHOLD:
            logger.info(
                f"STEEPENER SIGNAL ACTIVE: 2s10s spread ({spread:.2f}%) < "
                f"{self.SPREAD_STEEPENER_THRESHOLD}% threshold. "
                f"Adding {self.STEEPENER_EXTRA_ALLOCATION * 100:.0f}% extra to long treasuries."
            )
            return True, self.STEEPENER_EXTRA_ALLOCATION
        return False, 0.0

    def get_move_index(self) -> tuple[float, RateVolatilityRegime]:
        """
        Fetch MOVE Index (bond market volatility) and determine regime.

        The MOVE Index is the "VIX for bonds" - measures implied volatility
        of Treasury options. Low MOVE means safe to extend duration;
        high MOVE means reduce duration exposure to avoid 2022-style losses.

        Returns:
            tuple: (move_value, regime)
        """
        # Note: MOVE Index is available from FRED as "MOVE" or via CBOE
        # For now, we'll try FRED first, fall back to default
        if not self.fred_collector:
            logger.warning("FRED collector unavailable, assuming normal MOVE regime")
            return 100.0, RateVolatilityRegime.NORMAL

        try:
            # MOVE index from FRED (if available) or estimate from VIX correlation
            end_date = datetime.now()
            start_date = end_date - timedelta(days=7)

            # Try to fetch MOVE directly (may not be in FRED)
            # If not available, we'll use a proxy or default
            move_data = self.fred_collector._fetch_series(
                "MOVE",
                start_date.strftime("%Y-%m-%d"),
                end_date.strftime("%Y-%m-%d"),
            )

            if move_data and move_data.get("latest_value") not in (None, ".", ""):
                move_value = float(move_data["latest_value"])
            else:
                # Default to moderate level if unavailable
                logger.info("MOVE Index not available from FRED, using default 90")
                move_value = 90.0

        except Exception as e:
            logger.warning(f"Failed to fetch MOVE Index: {e}, using default 90")
            move_value = 90.0

        # Determine regime
        if move_value < self.MOVE_LOW_VOL_THRESHOLD:
            regime = RateVolatilityRegime.LOW
            logger.info(f"MOVE Index ({move_value:.0f}) LOW → Safe to extend duration")
        elif move_value > self.MOVE_HIGH_VOL_THRESHOLD:
            regime = RateVolatilityRegime.HIGH
            logger.info(f"MOVE Index ({move_value:.0f}) HIGH → Reduce duration exposure")
        else:
            regime = RateVolatilityRegime.NORMAL
            logger.info(f"MOVE Index ({move_value:.0f}) NORMAL → Standard allocation")

        return move_value, regime

    def apply_move_adjustment(
        self, allocation: dict[str, float], move_regime: RateVolatilityRegime
    ) -> dict[str, float]:
        """
        Adjust allocation based on MOVE Index volatility regime.

        Args:
            allocation: Base allocation percentages
            move_regime: Current rate volatility regime

        Returns:
            dict: Adjusted allocation percentages
        """
        if move_regime == RateVolatilityRegime.LOW:
            # Increase duration - boost TLT/ZROZ allocation
            multiplier = self.MOVE_DURATION_ADJUSTMENTS["low"]
            logger.info(f"LOW rate vol: Boosting long duration by {(multiplier - 1) * 100:.0f}%")
        elif move_regime == RateVolatilityRegime.HIGH:
            # Reduce duration - cut TLT/ZROZ, shift to SHY
            multiplier = self.MOVE_DURATION_ADJUSTMENTS["high"]
            logger.info(f"HIGH rate vol: Reducing long duration by {(1 - multiplier) * 100:.0f}%")
        else:
            multiplier = self.MOVE_DURATION_ADJUSTMENTS["normal"]

        adjusted = allocation.copy()

        # Adjust TLT allocation
        tlt_adjustment = adjusted.get("TLT", 0) * (multiplier - 1)
        adjusted["TLT"] = adjusted.get("TLT", 0) * multiplier

        # If reducing duration, shift excess to SHY
        if move_regime == RateVolatilityRegime.HIGH:
            shy_boost = -tlt_adjustment  # tlt_adjustment is negative
            adjusted["SHY"] = adjusted.get("SHY", 0) + shy_boost

        # Normalize to ensure sum = 1.0
        total = sum(adjusted.values())
        if total > 0:
            adjusted = {k: v / total for k, v in adjusted.items()}

        return adjusted

    def get_optimal_allocation(self) -> TreasuryAllocation:
        """
        Determine optimal allocation based on current yield curve, rate volatility,
        and steepener signals.

        Enhanced logic:
        1. Analyze yield curve regime (normal/flat/inverted)
        2. Check for steepener signal (2s10s < 0.2%)
        3. Get MOVE Index for rate volatility adjustment
        4. Select dynamic long ETF (TLT vs ZROZ based on 10Y yield)
        5. Apply all adjustments to create final allocation

        Returns:
            TreasuryAllocation dataclass with allocation percentages and metadata

        Example:
            >>> strategy = TreasuryLadderStrategy()
            >>> allocation = strategy.get_optimal_allocation()
            >>> print(f"SHY: {allocation.shy_pct*100:.0f}%, Long ETF: {allocation.long_etf}")
        """
        logger.info("=" * 60)
        logger.info("Calculating optimal treasury allocation (enhanced)...")

        # Step 1: Analyze yield curve
        regime, spread, rationale = self.analyze_yield_curve()

        # Step 2: Check steepener signal
        steepener_active, steepener_extra = self.check_steepener_signal(spread)

        # Step 3: Get MOVE Index and rate volatility regime
        move_value, move_regime = self.get_move_index()

        # Step 4: Get 10Y yield and select long ETF (TLT vs ZROZ)
        yield_10y = self.get_10y_yield()
        long_etf = self.select_long_etf(yield_10y)

        # Step 5: Select base allocation based on yield curve regime
        if regime == YieldCurveRegime.INVERTED:
            allocation_dict = self.ALLOCATION_INVERTED.copy()
        elif regime == YieldCurveRegime.FLAT:
            allocation_dict = self.ALLOCATION_FLAT.copy()
        else:  # NORMAL
            allocation_dict = self.ALLOCATION_NORMAL.copy()

        # Step 6: Apply steepener override if active
        if steepener_active:
            # Reduce SHY and IEF proportionally to fund extra long exposure
            shy_reduction = steepener_extra * 0.6  # 60% from SHY
            ief_reduction = steepener_extra * 0.4  # 40% from IEF
            allocation_dict["SHY"] = max(0.10, allocation_dict["SHY"] - shy_reduction)
            allocation_dict["IEF"] = max(0.10, allocation_dict["IEF"] - ief_reduction)
            allocation_dict["TLT"] = allocation_dict["TLT"] + steepener_extra
            logger.info(
                f"Steepener override applied: TLT boosted to {allocation_dict['TLT'] * 100:.0f}%"
            )

        # Step 7: Apply MOVE Index adjustment
        if move_regime != RateVolatilityRegime.NORMAL:
            allocation_dict = self.apply_move_adjustment(allocation_dict, move_regime)

        # Normalize to ensure sum = 1.0
        total = sum(allocation_dict.values())
        if abs(total - 1.0) > 0.001:
            allocation_dict = {k: v / total for k, v in allocation_dict.items()}

        # Build enhanced rationale
        enhanced_rationale = (
            f"{rationale} | "
            f"Long ETF: {long_etf} (10Y={yield_10y:.2f}%) | "
            f"MOVE: {move_value:.0f} ({move_regime.value})"
        )
        if steepener_active:
            enhanced_rationale += f" | STEEPENER ACTIVE (+{steepener_extra * 100:.0f}% long)"

        # Create allocation object with all enhancements
        allocation = TreasuryAllocation(
            shy_pct=allocation_dict["SHY"],
            ief_pct=allocation_dict["IEF"],
            tlt_pct=allocation_dict["TLT"],
            regime=regime,
            spread=spread,
            rationale=enhanced_rationale,
            timestamp=datetime.now(),
            long_etf=long_etf,
            govt_pct=self.GOVT_CORE_ALLOCATION,
            steepener_active=steepener_active,
            steepener_extra_pct=steepener_extra,
        )

        logger.info("=" * 60)
        logger.info("ENHANCED TREASURY ALLOCATION:")
        logger.info(f"  GOVT (fixed core): {allocation.govt_pct * 100:.0f}%")
        logger.info(f"  SHY (short): {allocation.shy_pct * 100:.0f}%")
        logger.info(f"  IEF (intermediate): {allocation.ief_pct * 100:.0f}%")
        logger.info(f"  {allocation.long_etf} (long): {allocation.tlt_pct * 100:.0f}%")
        logger.info(f"  Regime: {regime.value} | Spread: {spread:.2f}%")
        logger.info(f"  Steepener: {'ACTIVE' if steepener_active else 'inactive'}")
        logger.info("=" * 60)

        return allocation

    def execute_daily(self, amount: Optional[float] = None) -> dict[str, Any]:
        """
        Execute daily investment across enhanced treasury ladder.

        Enhanced execution with:
        1. Fixed 25% GOVT allocation (intermediate treasury for stable carry)
        2. Dynamic long ETF selection (TLT vs ZROZ based on 10Y yield)
        3. Steepener override when 2s10s spread < 0.2%
        4. MOVE Index adjustment for rate volatility

        Args:
            amount: Dollar amount to invest (default: self.daily_allocation)

        Returns:
            Dictionary containing execution results:
                - orders: List of executed orders
                - allocation: TreasuryAllocation used
                - total_invested: Total amount invested
                - success: Whether execution succeeded

        Example:
            >>> strategy = TreasuryLadderStrategy(daily_allocation=10.0)
            >>> result = strategy.execute_daily()
            >>> print(f"Invested ${result['total_invested']:.2f} in {result['allocation'].long_etf}")
        """
        amount = amount or self.daily_allocation

        logger.info("=" * 80)
        logger.info("Starting ENHANCED Treasury Ladder daily execution")
        logger.info(f"Investment amount: ${amount:.2f}")

        if not self.alpaca_trader:
            logger.error("Alpaca trader not initialized, cannot execute")
            return {
                "orders": [],
                "allocation": None,
                "total_invested": 0.0,
                "success": False,
                "error": "Alpaca trader not initialized",
            }

        try:
            # Get optimal allocation (includes dynamic ETF selection, steepener, MOVE)
            allocation = self.get_optimal_allocation()

            # Calculate dollar amounts for each ETF
            # GOVT gets fixed 25% core allocation
            govt_amount = amount * allocation.govt_pct

            # Remaining 75% goes to the dynamic ladder (SHY, IEF, TLT/ZROZ)
            ladder_amount = amount * (1 - allocation.govt_pct)
            shy_amount = ladder_amount * allocation.shy_pct
            ief_amount = ladder_amount * allocation.ief_pct
            long_amount = ladder_amount * allocation.tlt_pct

            # Use dynamic long ETF (TLT or ZROZ)
            long_etf = allocation.long_etf

            logger.info("=" * 60)
            logger.info("ALLOCATION BREAKDOWN:")
            logger.info(f"  GOVT (fixed core): ${govt_amount:.2f} (25%)")
            logger.info(f"  SHY (short): ${shy_amount:.2f}")
            logger.info(f"  IEF (intermediate): ${ief_amount:.2f}")
            logger.info(f"  {long_etf} (long): ${long_amount:.2f}")
            logger.info("=" * 60)

            # Execute orders
            orders = []
            total_invested = 0.0

            # Order execution list with dynamic long ETF
            execution_list = [
                ("GOVT", govt_amount),  # Fixed 25% core
                ("SHY", shy_amount),
                ("IEF", ief_amount),
                (long_etf, long_amount),  # Dynamic: TLT or ZROZ
            ]

            for symbol, invest_amount in execution_list:
                if invest_amount > 0.01:  # Skip if less than 1 cent
                    try:
                        order = self.alpaca_trader.execute_order(
                            symbol=symbol,
                            amount_usd=invest_amount,
                            side="buy",
                            tier="T1_CORE",  # Treat as core allocation
                        )
                        orders.append(order)
                        total_invested += invest_amount

                        logger.info(
                            f"Executed: BUY {symbol} ${invest_amount:.2f} (Order ID: {order['id']})"
                        )

                        # Update holdings tracking
                        self.current_holdings[symbol] = (
                            self.current_holdings.get(symbol, 0.0) + invest_amount
                        )

                    except Exception as e:
                        logger.error(f"Failed to execute order for {symbol}: {e}")
                        # Continue with other orders

            # Update total invested
            self.total_invested += total_invested

            logger.info("=" * 60)
            logger.info(
                f"Daily execution complete: {len(orders)} orders, ${total_invested:.2f} invested"
            )
            logger.info(f"Long ETF used: {long_etf}")
            if allocation.steepener_active:
                logger.info("STEEPENER OVERRIDE was active - extra long exposure")
            logger.info("=" * 60)

            return {
                "orders": orders,
                "allocation": allocation,
                "total_invested": total_invested,
                "success": len(orders) > 0,
                "timestamp": datetime.now().isoformat(),
                "long_etf": long_etf,
                "steepener_active": allocation.steepener_active,
            }

        except Exception as e:
            logger.error(f"Daily execution failed: {e}")
            return {
                "orders": [],
                "allocation": None,
                "total_invested": 0.0,
                "success": False,
                "error": str(e),
            }

    def rebalance_if_needed(self) -> Optional[RebalanceDecision]:
        """
        Check if rebalancing is needed and execute if necessary.

        Compares current holdings to target allocation. If any position
        drifts more than rebalance_threshold (default 5%), triggers a rebalance.

        Returns:
            RebalanceDecision if rebalance was checked, None if skipped

        Raises:
            Exception: If critical rebalancing error occurs

        Example:
            >>> strategy = TreasuryLadderStrategy()
            >>> decision = strategy.rebalance_if_needed()
            >>> if decision and decision.should_rebalance:
            ...     print(f"Rebalanced: {decision.reason}")
        """
        logger.info("Checking if rebalancing needed...")

        if not self.alpaca_trader:
            logger.warning("Alpaca trader not initialized, cannot rebalance")
            return None

        # Check minimum rebalancing interval
        if self.last_rebalance_date:
            days_since_rebalance = (datetime.now() - self.last_rebalance_date).days
            if days_since_rebalance < self.MIN_REBALANCE_INTERVAL_DAYS:
                logger.info(
                    f"Skipping rebalance check: Only {days_since_rebalance} days since last rebalance "
                    f"(minimum: {self.MIN_REBALANCE_INTERVAL_DAYS})"
                )
                return None

        try:
            # Get current positions from Alpaca
            positions = self.alpaca_trader.get_positions()

            # Filter to treasury positions
            treasury_positions = {
                pos["symbol"]: float(pos["market_value"])
                for pos in positions
                if pos["symbol"] in self.etf_symbols
            }

            # Calculate total treasury value
            total_value = sum(treasury_positions.values())

            if total_value < 1.0:
                logger.info("Treasury holdings too small to rebalance (< $1)")
                return None

            # Calculate current allocation percentages
            current_allocation = {
                symbol: treasury_positions.get(symbol, 0.0) / total_value
                for symbol in self.etf_symbols
            }

            # Get target allocation
            target_alloc_obj = self.get_optimal_allocation()
            target_allocation = {
                "SHY": target_alloc_obj.shy_pct,
                "IEF": target_alloc_obj.ief_pct,
                "TLT": target_alloc_obj.tlt_pct,
            }

            # Calculate drift for each position
            drift_pct = {
                symbol: abs(current_allocation[symbol] - target_allocation[symbol])
                for symbol in self.etf_symbols
            }

            max_drift = max(drift_pct.values())

            logger.info(
                f"Allocation drift: SHY={drift_pct['SHY'] * 100:.1f}%, "
                f"IEF={drift_pct['IEF'] * 100:.1f}%, TLT={drift_pct['TLT'] * 100:.1f}%"
            )

            # Determine if rebalancing needed
            should_rebalance = max_drift > self.rebalance_threshold

            if should_rebalance:
                reason = (
                    f"Max drift {max_drift * 100:.1f}% exceeds threshold "
                    f"{self.rebalance_threshold * 100:.1f}%"
                )
                logger.info(f"REBALANCING NEEDED: {reason}")

                # Execute rebalancing
                self._execute_rebalance(current_allocation, target_allocation, total_value)

                self.last_rebalance_date = datetime.now()
            else:
                reason = (
                    f"Max drift {max_drift * 100:.1f}% within threshold "
                    f"{self.rebalance_threshold * 100:.1f}%"
                )
                logger.info(f"No rebalancing needed: {reason}")

            # Create decision object
            decision = RebalanceDecision(
                should_rebalance=should_rebalance,
                current_allocation=current_allocation,
                target_allocation=target_allocation,
                drift_pct=drift_pct,
                max_drift=max_drift,
                reason=reason,
                timestamp=datetime.now(),
            )

            self.rebalance_history.append(decision)

            return decision

        except Exception as e:
            logger.error(f"Rebalancing check failed: {e}")
            return None

    def _execute_rebalance(
        self,
        current_allocation: dict[str, float],
        target_allocation: dict[str, float],
        total_value: float,
    ) -> None:
        """
        Execute rebalancing trades to align with target allocation.

        Args:
            current_allocation: Current allocation percentages by symbol
            target_allocation: Target allocation percentages by symbol
            total_value: Total portfolio value in dollars

        Raises:
            Exception: If rebalancing execution fails
        """
        logger.info("Executing rebalancing trades...")

        for symbol in self.etf_symbols:
            current_pct = current_allocation[symbol]
            target_pct = target_allocation[symbol]

            # Calculate dollar difference
            current_value = current_pct * total_value
            target_value = target_pct * total_value
            delta_value = target_value - current_value

            # Skip if change is too small
            if abs(delta_value) < 1.0:
                logger.info(f"Skipping {symbol}: delta ${delta_value:.2f} too small")
                continue

            try:
                if delta_value > 0:
                    # Need to buy more
                    logger.info(f"Rebalance: BUY {symbol} ${delta_value:.2f}")
                    self.alpaca_trader.execute_order(
                        symbol=symbol,
                        amount_usd=delta_value,
                        side="buy",
                        tier="T1_CORE",
                    )
                else:
                    # Need to sell some
                    sell_amount = abs(delta_value)
                    logger.info(f"Rebalance: SELL {symbol} ${sell_amount:.2f}")

                    # Get current position to calculate quantity
                    positions = self.alpaca_trader.get_positions()
                    pos = next((p for p in positions if p["symbol"] == symbol), None)

                    if pos:
                        # Calculate shares to sell
                        current_qty = float(pos["qty"])
                        current_market_value = float(pos["market_value"])
                        sell_qty = (sell_amount / current_market_value) * current_qty

                        # Execute sell order
                        # Note: AlpacaTrader.execute_order doesn't support qty-based sells
                        # We'd need to use a different method or close partial position
                        logger.warning(
                            f"Sell rebalancing not fully implemented for {symbol} "
                            f"(would sell {sell_qty:.4f} shares)"
                        )
                    else:
                        logger.warning(f"Could not find position for {symbol} to rebalance")

            except Exception as e:
                logger.error(f"Failed to rebalance {symbol}: {e}")
                # Continue with other symbols

        logger.info("Rebalancing execution complete")

    def get_performance_summary(self) -> dict[str, Any]:
        """
        Get performance summary for treasury ladder.

        Returns:
            Dictionary containing performance metrics
        """
        try:
            if not self.alpaca_trader:
                return {"error": "Alpaca trader not initialized"}

            # Get current positions
            positions = self.alpaca_trader.get_positions()
            treasury_positions = [pos for pos in positions if pos["symbol"] in self.etf_symbols]

            total_market_value = sum(float(pos["market_value"]) for pos in treasury_positions)
            total_cost_basis = sum(float(pos["cost_basis"]) for pos in treasury_positions)
            total_unrealized_pl = sum(float(pos["unrealized_pl"]) for pos in treasury_positions)

            return {
                "total_invested": self.total_invested,
                "total_market_value": total_market_value,
                "total_cost_basis": total_cost_basis,
                "total_unrealized_pl": total_unrealized_pl,
                "return_pct": (
                    (total_unrealized_pl / total_cost_basis * 100) if total_cost_basis > 0 else 0.0
                ),
                "positions": treasury_positions,
                "current_regime": self.current_regime.value if self.current_regime else "unknown",
                "last_rebalance": (
                    self.last_rebalance_date.isoformat() if self.last_rebalance_date else None
                ),
                "rebalance_count": len(self.rebalance_history),
                "timestamp": datetime.now().isoformat(),
            }

        except Exception as e:
            logger.error(f"Failed to get performance summary: {e}")
            return {"error": str(e)}


if __name__ == "__main__":
    """
    Example usage and testing.
    """
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    # Initialize strategy
    strategy = TreasuryLadderStrategy(
        daily_allocation=10.0,
        rebalance_threshold=0.05,
        paper=True,
    )

    print("\n" + "=" * 80)
    print("TREASURY LADDER STRATEGY - DEMO")
    print("=" * 80)

    # Analyze yield curve
    print("\n1. YIELD CURVE ANALYSIS")
    regime, spread, rationale = strategy.analyze_yield_curve()
    print(f"   Regime: {regime.value}")
    print(f"   Spread: {spread:.2f}%")
    print(f"   Rationale: {rationale}")

    # Get optimal allocation
    print("\n2. OPTIMAL ALLOCATION")
    allocation = strategy.get_optimal_allocation()
    print(f"   SHY (1-3yr): {allocation.shy_pct * 100:.0f}%")
    print(f"   IEF (7-10yr): {allocation.ief_pct * 100:.0f}%")
    print(f"   TLT (20+yr): {allocation.tlt_pct * 100:.0f}%")

    # Execute daily (demo - will actually trade if Alpaca configured)
    print("\n3. DAILY EXECUTION (DEMO)")
    print("   Would invest $10 across ladder...")
    # Uncomment to actually execute:
    # result = strategy.execute_daily()
    # print(f"   Orders executed: {len(result['orders'])}")
    # print(f"   Total invested: ${result['total_invested']:.2f}")

    # Check rebalancing
    print("\n4. REBALANCING CHECK")
    print("   Would check if rebalancing needed...")
    # Uncomment to actually check:
    # decision = strategy.rebalance_if_needed()
    # if decision:
    #     print(f"   Should rebalance: {decision.should_rebalance}")
    #     print(f"   Reason: {decision.reason}")

    print("\n" + "=" * 80)
    print("Demo complete!")
    print("=" * 80 + "\n")
