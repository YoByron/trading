"""
Phil Town Rule #1 Options Strategy

Implements Phil Town's Rule #1 investing approach with options:
1. Sticker Price Calculator - Intrinsic value based on growth rate
2. Margin of Safety (MOS) - Buy price at 50% discount
3. Selling Puts to Buy at Discount - "Getting Paid to Wait"
4. Selling Covered Calls - "Getting Paid to Sell"
5. Big Five Analysis - Quality screening

Reference: "Rule #1" and "Payback Time" by Phil Town

Key Principles:
- Only trade options on "wonderful companies" you'd want to own
- Sell puts at MOS price (50% below Sticker Price)
- Sell calls at Sticker Price (fair value)
- 10-year horizon for valuation
- 15% Minimum Acceptable Rate of Return (MARR)
"""

import json
import logging
import os
import time
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Optional

import numpy as np
import requests
import yfinance as yf

logger = logging.getLogger(__name__)

# Rate limiting for Yahoo Finance fallback
_LAST_YFINANCE_CALL = 0.0
_YFINANCE_MIN_INTERVAL = 0.5  # 500ms between calls

try:
    from src.core.alpaca_trader import AlpacaTrader
    from src.core.options_client import AlpacaOptionsClient
except ModuleNotFoundError:  # pragma: no cover - fallback for lightweight test envs
    logger.warning("Falling back to stubbed Alpaca clients (dependency not available).")

    class AlpacaTrader:  # type: ignore[override]
        """Minimal stub used only for unit tests when full stack deps are unavailable."""

        def __init__(self, *args, **kwargs) -> None:
            self._account = {"cash": "0"}

        def get_account(self) -> dict[str, str]:
            return self._account

        def get_positions(self) -> list[dict[str, str]]:
            return []

    class AlpacaOptionsClient:  # type: ignore[override]
        """Minimal stub used only for unit tests when full stack deps are unavailable."""

        def __init__(self, *args, **kwargs) -> None:
            pass


class MeaningRating(Enum):
    """Phil Town's 'Meaning' rating - do you understand the business?"""

    EXCELLENT = "excellent"  # Fully understand, use products
    GOOD = "good"  # Understand well
    FAIR = "fair"  # Basic understanding
    POOR = "poor"  # Don't understand


class MoatRating(Enum):
    """Phil Town's 'Moat' rating - competitive advantage durability."""

    WIDE = "wide"  # Strong, durable advantage (brand, network, patents)
    NARROW = "narrow"  # Some advantage but vulnerable
    NONE = "none"  # No sustainable advantage


class ManagementRating(Enum):
    """Phil Town's 'Management' rating - quality of leadership."""

    EXCELLENT = "excellent"  # Owner-oriented, high integrity
    GOOD = "good"  # Competent, shareholder-friendly
    FAIR = "fair"  # Mixed track record
    POOR = "poor"  # Avoid


@dataclass
class BigFiveMetrics:
    """Phil Town's Big Five Numbers for quality analysis."""

    roic: float  # Return on Invested Capital
    equity_growth: float  # Book Value per Share growth
    eps_growth: float  # Earnings per Share growth
    sales_growth: float  # Revenue growth
    fcf_growth: float  # Free Cash Flow growth

    # Calculated fields
    avg_growth: float = 0.0
    passes_rule_one: bool = False

    def __post_init__(self):
        """Calculate average growth and Rule #1 pass/fail."""
        growth_rates = [self.equity_growth, self.eps_growth, self.sales_growth, self.fcf_growth]
        valid_rates = [r for r in growth_rates if r is not None and not np.isnan(r)]
        self.avg_growth = np.mean(valid_rates) if valid_rates else 0.0

        # Rule #1: All Big Five should be >= 10% over 10, 5, and 1 year
        # Simplified: Average growth >= 10% and ROIC >= 10%
        self.passes_rule_one = bool(
            self.avg_growth >= 0.10 and self.roic is not None and self.roic >= 0.10
        )


@dataclass
class StickerPriceResult:
    """Phil Town's Sticker Price calculation result."""

    symbol: str
    current_price: float
    current_eps: float
    growth_rate: float  # Estimated future EPS growth
    future_eps: float  # EPS in 10 years
    future_pe: float  # P/E ratio in 10 years
    future_price: float  # Price in 10 years
    sticker_price: float  # Fair value today (discounted)
    mos_price: float  # Margin of Safety price (50% discount)

    # Analysis
    upside_to_sticker: float = 0.0  # % upside to fair value
    margin_of_safety: float = 0.0  # Current MOS %
    recommendation: str = ""
    timestamp: datetime = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()

        if self.current_price > 0:
            self.upside_to_sticker = (self.sticker_price - self.current_price) / self.current_price
            self.margin_of_safety = (self.sticker_price - self.current_price) / self.sticker_price

            if self.current_price <= self.mos_price:
                self.recommendation = "STRONG BUY - Below MOS Price"
            elif self.current_price <= self.sticker_price:
                self.recommendation = "BUY - Below Sticker Price"
            elif self.current_price <= self.sticker_price * 1.2:
                self.recommendation = "HOLD - Near Fair Value"
            else:
                self.recommendation = "SELL - Overvalued"


@dataclass
class RuleOneOptionsSignal:
    """Signal for Rule #1 options trade."""

    symbol: str
    signal_type: str  # 'sell_put' or 'sell_call'
    strike: float
    expiration: str
    premium: float
    annualized_return: float
    sticker_price: float
    mos_price: float
    current_price: float
    rationale: str
    confidence: float  # 0.0 to 1.0
    contracts: int = 1
    total_premium: float = 0.0
    iv_rank: Optional[float] = None
    delta: Optional[float] = None
    days_to_expiry: Optional[int] = None
    timestamp: datetime = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


@dataclass
class OptionContract:
    """Lightweight container for option chain selections."""

    symbol: str
    option_type: str  # 'put' or 'call'
    expiration: str
    strike: float
    bid: float
    ask: float
    mid: float
    delta: Optional[float]
    implied_vol: Optional[float]
    days_to_expiry: int
    iv_rank: Optional[float] = None


class RuleOneOptionsStrategy:
    """
    Phil Town's Rule #1 Options Strategy.

    Two core strategies:
    1. Selling Puts to Buy at Discount ("Getting Paid to Wait")
       - Sell cash-secured puts at MOS price
       - If assigned, you own the stock at your target price minus premium
       - If not assigned, keep premium as profit

    2. Selling Covered Calls ("Getting Paid to Sell")
       - Own shares first, then sell calls at Sticker Price
       - If called away, sell at fair value plus premium
       - If not called, keep premium and shares

    Key Requirements:
    - Only on "wonderful companies" (pass Big Five test)
    - Strike price based on Sticker Price / MOS Price
    - 30-45 days to expiration (optimal theta decay)
    - Minimum 12% annualized return on premium
    """

    # Phil Town's constants
    MARR = 0.15  # Minimum Acceptable Rate of Return (15%)
    MOS_DISCOUNT = 0.50  # 50% Margin of Safety
    DEFAULT_PE_RATIO_CAP = 50  # Maximum P/E ratio to use
    PROJECTION_YEARS = 10  # Project growth 10 years forward

    # Options parameters
    MIN_DAYS_TO_EXPIRY = 25
    MAX_DAYS_TO_EXPIRY = 50
    # Conservative delta targets (CEO directive Dec 2, 2025)
    # Lower delta = lower risk of assignment, safer for beginners
    TARGET_DELTA_PUT = 0.20  # ~20% chance of assignment (was 0.30)
    TARGET_DELTA_CALL = 0.25  # ~25% chance of being called away (was 0.30)
    DELTA_TOLERANCE = 0.05  # Allow small variance around target

    # IV Rank filter - only sell premium when IV is low
    # High IV = expensive options = higher premium but more risk
    MAX_IV_RANK = 40  # Only sell when IV rank < 40 (options are cheap)

    # Premium cap - never receive more than 1.2% of underlying per trade
    MAX_PREMIUM_PCT = 0.012  # 1.2% of stock price max
    MIN_ANNUALIZED_RETURN = 0.12  # 12% minimum annualized yield

    # Default wonderful companies (Rule #1 quality stocks)
    DEFAULT_UNIVERSE = [
        "AAPL",
        "MSFT",
        "GOOGL",
        "AMZN",
        "BRK-B",  # Large cap quality
        "V",
        "MA",
        "JNJ",
        "PG",
        "KO",  # Consumer/Financial moats
        "NVDA",
        "COST",
        "UNH",
        "HD",
        "MCD",  # Growth + moat
    ]

    # Cache settings
    CACHE_TTL_HOURS = 24  # Fundamentals cache valid for 24 hours

    def __init__(
        self,
        paper: bool = True,
        universe: Optional[list[str]] = None,
        min_shares_for_calls: int = 100,
    ):
        """
        Initialize Rule #1 Options Strategy.

        Args:
            paper: Use paper trading if True
            universe: List of symbols to analyze (defaults to quality stocks)
            min_shares_for_calls: Minimum shares needed for covered calls
        """
        self.paper = paper
        self.universe = universe or self.DEFAULT_UNIVERSE
        self.min_shares_for_calls = min_shares_for_calls

        # Initialize trading clients
        self.trader = AlpacaTrader(paper=paper)
        self.options_client = AlpacaOptionsClient(paper=paper)
        self.options_log_dir = Path("data/options_signals")

        # File-based cache directory for fundamentals
        self.fundamentals_cache_dir = Path("data/cache/fundamentals")
        self.fundamentals_cache_dir.mkdir(parents=True, exist_ok=True)

        # In-memory cache for valuations (session-only)
        self._valuation_cache: dict[str, StickerPriceResult] = {}
        self._big_five_cache: dict[str, BigFiveMetrics] = {}

        logger.info(
            f"Rule #1 Options Strategy initialized: {len(self.universe)} symbols, paper={paper}"
        )

    def _load_cached_fundamentals(self, symbol: str) -> Optional[dict]:
        """Load cached fundamentals from disk if fresh."""
        cache_file = self.fundamentals_cache_dir / f"{symbol}_fundamentals.json"
        if not cache_file.exists():
            return None

        try:
            with open(cache_file) as f:
                data = json.load(f)

            # Check TTL
            cached_time = datetime.fromisoformat(data.get("timestamp", "2000-01-01"))
            age_hours = (datetime.now() - cached_time).total_seconds() / 3600

            if age_hours > self.CACHE_TTL_HOURS:
                logger.debug(
                    f"{symbol}: Cache expired ({age_hours:.1f}h > {self.CACHE_TTL_HOURS}h)"
                )
                return None

            logger.debug(f"{symbol}: Using cached fundamentals ({age_hours:.1f}h old)")
            return data
        except Exception as e:
            logger.debug(f"{symbol}: Failed to load cache: {e}")
            return None

    def _save_cached_fundamentals(self, symbol: str, data: dict) -> None:
        """Save fundamentals to disk cache."""
        cache_file = self.fundamentals_cache_dir / f"{symbol}_fundamentals.json"
        try:
            data["timestamp"] = datetime.now().isoformat()
            with open(cache_file, "w") as f:
                json.dump(data, f, indent=2)
            logger.debug(f"{symbol}: Fundamentals cached to disk")
        except Exception as e:
            logger.debug(f"{symbol}: Failed to save cache: {e}")

    def _fetch_polygon_fundamentals(self, symbol: str) -> Optional[dict]:
        """
        Fetch fundamental data from Polygon.io API.

        Returns dict with growth rates and financial metrics, or None if unavailable.
        """
        polygon_api_key = os.getenv("POLYGON_API_KEY")
        if not polygon_api_key:
            return None

        try:
            # Polygon.io v3 ticker details endpoint
            url = f"https://api.polygon.io/v3/reference/tickers/{symbol}"
            params = {"apiKey": polygon_api_key}
            response = requests.get(url, params=params, timeout=15)

            if response.status_code == 429:
                logger.warning(f"Polygon.io rate limited for {symbol}")
                return None

            response.raise_for_status()
            data = response.json()

            if data.get("status") != "OK":
                return None

            result = data.get("results", {})
            if not result:
                return None

            logger.debug(f"Polygon.io fundamentals fetched for {symbol}")
            return {
                "source": "polygon",
                "market_cap": result.get("market_cap"),
                "shares_outstanding": result.get("share_class_shares_outstanding"),
                "name": result.get("name"),
            }
        except Exception as e:
            logger.debug(f"Polygon.io fundamentals failed for {symbol}: {e}")
            return None

    def _fetch_finnhub_fundamentals(self, symbol: str) -> Optional[dict]:
        """
        Fetch fundamental data from Finnhub API.

        Returns dict with growth rates and financial metrics, or None if unavailable.
        """
        finnhub_api_key = os.getenv("FINNHUB_API_KEY")
        if not finnhub_api_key:
            return None

        try:
            # Finnhub basic financials endpoint
            url = "https://finnhub.io/api/v1/stock/metric"
            params = {"symbol": symbol, "metric": "all", "token": finnhub_api_key}
            response = requests.get(url, params=params, timeout=15)

            if response.status_code == 429:
                logger.warning(f"Finnhub rate limited for {symbol}")
                return None

            response.raise_for_status()
            data = response.json()

            metrics = data.get("metric", {})
            if not metrics:
                return None

            logger.debug(f"Finnhub fundamentals fetched for {symbol}")
            return {
                "source": "finnhub",
                "roic": metrics.get("roicTTM"),
                "eps_growth_5y": metrics.get("epsGrowth5Y"),
                "revenue_growth_5y": metrics.get("revenueGrowth5Y"),
                "pe_ratio": metrics.get("peBasicExclExtraTTM"),
                "book_value_growth_5y": metrics.get("bookValuePerShareGrowth5Y"),
            }
        except Exception as e:
            logger.debug(f"Finnhub fundamentals failed for {symbol}: {e}")
            return None

    def _fetch_yfinance_fundamentals(self, symbol: str) -> Optional[dict]:
        """
        Fetch fundamental data from Yahoo Finance (fallback).

        Returns dict with growth rates and financial metrics, or None if unavailable.
        """
        global _LAST_YFINANCE_CALL

        # Rate limiting
        elapsed = time.time() - _LAST_YFINANCE_CALL
        if elapsed < _YFINANCE_MIN_INTERVAL:
            time.sleep(_YFINANCE_MIN_INTERVAL - elapsed)
        _LAST_YFINANCE_CALL = time.time()

        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info

            if not info or "symbol" not in info:
                return None

            logger.debug(f"Yahoo Finance fundamentals fetched for {symbol}")
            return {
                "source": "yfinance",
                "roic": info.get("returnOnCapital") or info.get("returnOnEquity"),
                "eps_growth": info.get("earningsGrowth"),
                "revenue_growth": info.get("revenueGrowth"),
                "current_price": info.get("currentPrice") or info.get("regularMarketPrice"),
                "trailing_eps": info.get("trailingEps"),
                "forward_pe": info.get("forwardPE"),
            }
        except Exception as e:
            logger.debug(f"Yahoo Finance fundamentals failed for {symbol}: {e}")
            return None

    def calculate_big_five(self, symbol: str) -> Optional[BigFiveMetrics]:
        """
        Calculate Phil Town's Big Five metrics for a stock.

        Uses disk cache (24h TTL) + multi-source fallback: Finnhub -> Yahoo Finance

        Args:
            symbol: Stock ticker

        Returns:
            BigFiveMetrics or None if data unavailable
        """
        # Check in-memory cache first
        if symbol in self._big_five_cache:
            return self._big_five_cache[symbol]

        try:
            # Check disk cache
            cached = self._load_cached_fundamentals(symbol)
            if cached and cached.get("big_five"):
                bf = cached["big_five"]
                metrics = BigFiveMetrics(
                    roic=bf.get("roic", 0.10),
                    equity_growth=bf.get("equity_growth", 0.10),
                    eps_growth=bf.get("eps_growth", 0.10),
                    sales_growth=bf.get("sales_growth", 0.10),
                    fcf_growth=bf.get("fcf_growth", 0.10),
                )
                self._big_five_cache[symbol] = metrics
                logger.info(
                    f"{symbol}: Big Five from cache - ROIC={metrics.roic:.1%}, EPS Growth={metrics.eps_growth:.1%}"
                )
                return metrics

            # Try Finnhub first (has growth metrics)
            finnhub_data = self._fetch_finnhub_fundamentals(symbol)
            if finnhub_data:
                roic = finnhub_data.get("roic") or 0.10
                eps_growth = (finnhub_data.get("eps_growth_5y") or 10.0) / 100.0
                revenue_growth = (finnhub_data.get("revenue_growth_5y") or 10.0) / 100.0
                equity_growth = (
                    finnhub_data.get("book_value_growth_5y") or eps_growth * 80
                ) / 100.0

                metrics = BigFiveMetrics(
                    roic=roic if roic else 0.10,
                    equity_growth=equity_growth,
                    eps_growth=eps_growth,
                    sales_growth=revenue_growth,
                    fcf_growth=eps_growth * 0.9,
                )
                self._big_five_cache[symbol] = metrics

                # Save to disk cache
                self._save_cached_fundamentals(
                    symbol,
                    {
                        "source": "finnhub",
                        "big_five": {
                            "roic": metrics.roic,
                            "equity_growth": metrics.equity_growth,
                            "eps_growth": metrics.eps_growth,
                            "sales_growth": metrics.sales_growth,
                            "fcf_growth": metrics.fcf_growth,
                        },
                    },
                )

                logger.info(
                    f"{symbol}: Big Five from Finnhub - ROIC={roic:.1%}, EPS Growth={eps_growth:.1%}"
                )
                return metrics

            # Try Yahoo Finance as fallback
            yf_data = self._fetch_yfinance_fundamentals(symbol)
            if yf_data:
                roic = yf_data.get("roic") or 0.10
                eps_growth = yf_data.get("eps_growth") or 0.10
                revenue_growth = yf_data.get("revenue_growth") or 0.10

                metrics = BigFiveMetrics(
                    roic=roic,
                    equity_growth=eps_growth * 0.8 if eps_growth else 0.10,
                    eps_growth=eps_growth,
                    sales_growth=revenue_growth,
                    fcf_growth=eps_growth * 0.9 if eps_growth else 0.10,
                )
                self._big_five_cache[symbol] = metrics

                # Save to disk cache
                self._save_cached_fundamentals(
                    symbol,
                    {
                        "source": "yfinance",
                        "big_five": {
                            "roic": metrics.roic,
                            "equity_growth": metrics.equity_growth,
                            "eps_growth": metrics.eps_growth,
                            "sales_growth": metrics.sales_growth,
                            "fcf_growth": metrics.fcf_growth,
                        },
                    },
                )

                logger.info(
                    f"{symbol}: Big Five from Yahoo Finance - ROIC={roic:.1%}, EPS Growth={eps_growth:.1%}"
                )
                return metrics

            # All sources failed - use conservative defaults
            logger.warning(f"{symbol}: All fundamental sources failed, using defaults")
            metrics = BigFiveMetrics(
                roic=0.10,
                equity_growth=0.08,
                eps_growth=0.08,
                sales_growth=0.08,
                fcf_growth=0.08,
            )
            self._big_five_cache[symbol] = metrics
            return metrics

        except Exception as e:
            logger.warning(f"Failed to calculate Big Five for {symbol}: {e}")
            return None

    def _fetch_current_price(self, symbol: str) -> Optional[float]:
        """
        Fetch current stock price from multiple sources.

        Priority: Alpaca -> Polygon.io -> Yahoo Finance
        """
        # Try Alpaca first (most reliable for our trading system)
        try:
            if hasattr(self.trader, "get_latest_quote"):
                quote = self.trader.get_latest_quote(symbol)
                if quote and quote.get("price"):
                    return float(quote["price"])
        except Exception:
            pass

        # Try Polygon.io
        polygon_api_key = os.getenv("POLYGON_API_KEY")
        if polygon_api_key:
            try:
                url = f"https://api.polygon.io/v2/aggs/ticker/{symbol}/prev"
                params = {"apiKey": polygon_api_key}
                response = requests.get(url, params=params, timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    results = data.get("results", [])
                    if results:
                        return float(results[0].get("c", 0))  # Close price
            except Exception:
                pass

        # Fallback to Yahoo Finance with rate limiting
        global _LAST_YFINANCE_CALL
        elapsed = time.time() - _LAST_YFINANCE_CALL
        if elapsed < _YFINANCE_MIN_INTERVAL:
            time.sleep(_YFINANCE_MIN_INTERVAL - elapsed)
        _LAST_YFINANCE_CALL = time.time()

        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info
            return info.get("currentPrice") or info.get("regularMarketPrice")
        except Exception:
            return None

    def calculate_sticker_price(self, symbol: str) -> Optional[StickerPriceResult]:
        """
        Calculate Phil Town's Sticker Price and MOS Price.

        Uses multi-source fallback for price and fundamentals data.

        Formula:
        1. Get current EPS
        2. Estimate growth rate (from Big Five or analysts)
        3. Future EPS = Current EPS * (1 + growth)^10
        4. Future P/E = min(2 * growth_rate * 100, 50)
        5. Future Price = Future EPS * Future P/E
        6. Sticker Price = Future Price / (1 + MARR)^10
        7. MOS Price = Sticker Price * 0.50

        Args:
            symbol: Stock ticker

        Returns:
            StickerPriceResult or None if calculation fails
        """
        try:
            # Get current price from multiple sources
            current_price = self._fetch_current_price(symbol)
            if not current_price or current_price <= 0:
                logger.warning(f"{symbol}: Unable to fetch current price")
                return None

            # Get fundamentals (already uses multi-source fallback)
            yf_data = self._fetch_yfinance_fundamentals(symbol)
            current_eps = yf_data.get("trailing_eps") if yf_data else None

            if not current_eps or current_eps <= 0:
                logger.warning(f"{symbol}: Negative or zero EPS, skipping")
                return None

            # Get Big Five for growth estimate (uses multi-source)
            big_five = self._big_five_cache.get(symbol) or self.calculate_big_five(symbol)

            if big_five and big_five.avg_growth > 0:
                growth_rate = min(big_five.avg_growth, 0.25)  # Cap at 25%
            else:
                growth_rate = 0.10  # Conservative default

            # Phil Town's formula
            # Step 1: Project EPS 10 years forward
            future_eps = current_eps * ((1 + growth_rate) ** self.PROJECTION_YEARS)

            # Step 2: Estimate future P/E (2x growth rate, capped at 50)
            future_pe = min(growth_rate * 100 * 2, self.DEFAULT_PE_RATIO_CAP)
            future_pe = max(future_pe, 8)  # Floor at 8x P/E

            # Step 3: Calculate future price
            future_price = future_eps * future_pe

            # Step 4: Discount back at MARR (15%)
            sticker_price = future_price / ((1 + self.MARR) ** self.PROJECTION_YEARS)

            # Step 5: Apply Margin of Safety (50% discount)
            mos_price = sticker_price * self.MOS_DISCOUNT

            result = StickerPriceResult(
                symbol=symbol,
                current_price=current_price,
                current_eps=current_eps,
                growth_rate=growth_rate,
                future_eps=future_eps,
                future_pe=future_pe,
                future_price=future_price,
                sticker_price=sticker_price,
                mos_price=mos_price,
            )

            self._valuation_cache[symbol] = result
            logger.info(
                f"{symbol}: Sticker Price=${sticker_price:.2f}, MOS=${mos_price:.2f}, "
                f"Current=${current_price:.2f}, Growth={growth_rate:.1%}"
            )
            return result

        except Exception as e:
            logger.error(f"Failed to calculate Sticker Price for {symbol}: {e}")
            return None

    def _get_available_cash(self) -> float:
        """Fetch available cash/buying power for sizing put contracts."""
        try:
            # Use get_account_info (correct method) with fallback to get_account
            if hasattr(self.trader, "get_account_info"):
                account = self.trader.get_account_info()
            else:
                account = self.trader.get_account()

            cash_fields = [
                account.get("cash"),
                account.get("buying_power"),
                account.get("equity"),
            ]
            for value in cash_fields:
                if value is None:
                    continue
                try:
                    cash_val = float(value)
                    if cash_val > 0:
                        logger.debug(f"Available cash for options: ${cash_val:,.2f}")
                        return cash_val
                except (TypeError, ValueError):
                    continue
        except Exception as exc:
            logger.error(f"Unable to load account cash for options sizing: {exc}")
        return 0.0

    @staticmethod
    def _compute_iv_rank(implied_vols, current_iv: Optional[float]) -> Optional[float]:
        """
        Approximate IV rank (0-100) using min/max IV from current option chain.
        """
        try:
            if current_iv is None or np.isnan(current_iv):
                return None

            clean = [
                float(iv) for iv in implied_vols if iv is not None and not np.isnan(iv) and iv > 0
            ]
            if len(clean) < 5:
                return None

            iv_min = min(clean)
            iv_max = max(clean)
            if iv_max <= iv_min:
                return None

            rank = (float(current_iv) - iv_min) / (iv_max - iv_min)
            rank = max(0.0, min(rank, 1.0))
            return round(rank * 100, 2)
        except Exception:
            return None

    @staticmethod
    def _serialize_signal(signal: RuleOneOptionsSignal) -> dict:
        """Convert signal dataclass into JSON-friendly dict."""
        payload = {
            "symbol": signal.symbol,
            "type": signal.signal_type,
            "strike": signal.strike,
            "expiration": signal.expiration,
            "premium": signal.premium,
            "total_premium": signal.total_premium,
            "annualized_return": signal.annualized_return,
            "contracts": signal.contracts,
            "sticker_price": signal.sticker_price,
            "mos_price": signal.mos_price,
            "current_price": signal.current_price,
            "iv_rank": signal.iv_rank,
            "delta": signal.delta,
            "days_to_expiry": signal.days_to_expiry,
            "confidence": signal.confidence,
            "rationale": signal.rationale,
            "timestamp": signal.timestamp.isoformat(),
        }
        return payload

    @staticmethod
    def _serialize_valuation(result: StickerPriceResult) -> dict:
        """Convert StickerPriceResult to JSON-friendly dict."""
        return {
            "symbol": result.symbol,
            "current_price": result.current_price,
            "sticker_price": result.sticker_price,
            "mos_price": result.mos_price,
            "growth_rate": result.growth_rate,
            "future_pe": result.future_pe,
            "recommendation": result.recommendation,
            "upside_to_sticker": result.upside_to_sticker,
            "margin_of_safety": result.margin_of_safety,
            "timestamp": result.timestamp.isoformat() if result.timestamp else None,
        }

    def _persist_signals(self, snapshot: dict) -> None:
        """Persist daily signals to disk for audit trail."""
        try:
            self.options_log_dir.mkdir(parents=True, exist_ok=True)
            filename = datetime.now().strftime("%Y-%m-%d.json")
            filepath = self.options_log_dir / filename
            with open(filepath, "w", encoding="utf-8") as handle:
                json.dump(snapshot, handle, indent=2)
            logger.info(f"Saved options snapshot → {filepath}")
        except Exception as exc:
            logger.error(f"Failed to persist options snapshot: {exc}")

    def find_put_opportunities(self) -> list[RuleOneOptionsSignal]:
        """
        Find opportunities to sell puts at MOS price.

        "Getting Paid to Wait" strategy:
        - Find stocks trading ABOVE their MOS price
        - Sell puts at strike near MOS price
        - If assigned, you get the stock at your target
        - If not, you keep the premium

        Returns:
            List of RuleOneOptionsSignal for put selling opportunities
        """
        signals: list[RuleOneOptionsSignal] = []
        cash_available = self._get_available_cash()

        if cash_available <= 0:
            logger.warning("No available cash for put selling; skipping opportunities.")
            return signals

        for symbol in self.universe:
            try:
                valuation = self._valuation_cache.get(symbol) or self.calculate_sticker_price(
                    symbol
                )
                if not valuation:
                    continue

                big_five = self._big_five_cache.get(symbol)
                if big_five and not big_five.passes_rule_one:
                    logger.debug(f"{symbol}: Fails Big Five test, skipping")
                    continue

                if valuation.current_price < valuation.mos_price:
                    logger.info(f"{symbol}: Below MOS ${valuation.mos_price:.2f}, just BUY")
                    continue

                target_strike = valuation.mos_price
                contract = self._find_best_put_option(symbol, target_strike)
                if not contract or contract.mid <= 0:
                    continue

                # Enforce IV rank + delta gates
                if contract.iv_rank is not None and contract.iv_rank > self.MAX_IV_RANK:
                    logger.debug(
                        f"{symbol}: IV rank {contract.iv_rank:.1f} exceeds max {self.MAX_IV_RANK}"
                    )
                    continue

                if contract.delta is not None and abs(contract.delta) > (
                    self.TARGET_DELTA_PUT + self.DELTA_TOLERANCE
                ):
                    logger.debug(
                        f"{symbol}: Put delta {contract.delta:.2f} too high for target {self.TARGET_DELTA_PUT}"
                    )
                    continue

                premium_pct = (
                    contract.mid / valuation.current_price if valuation.current_price else 0
                )
                if premium_pct > self.MAX_PREMIUM_PCT:
                    logger.debug(
                        f"{symbol}: Premium {premium_pct:.2%} exceeds cap {self.MAX_PREMIUM_PCT:.2%}"
                    )
                    continue

                if contract.days_to_expiry <= 0:
                    continue

                annualized_return = (contract.mid / target_strike) * (365 / contract.days_to_expiry)
                if annualized_return < self.MIN_ANNUALIZED_RETURN:
                    logger.debug(
                        f"{symbol}: Annualized return {annualized_return:.1%} below minimum"
                    )
                    continue

                max_contracts = int(cash_available // (target_strike * 100))
                if max_contracts <= 0:
                    logger.debug(
                        f"{symbol}: Not enough cash (${cash_available:.2f}) for cash-secured puts"
                    )
                    continue

                total_premium = contract.mid * 100 * max_contracts
                signal = RuleOneOptionsSignal(
                    symbol=symbol,
                    signal_type="sell_put",
                    strike=target_strike,
                    expiration=contract.expiration,
                    premium=contract.mid,
                    annualized_return=annualized_return,
                    sticker_price=valuation.sticker_price,
                    mos_price=valuation.mos_price,
                    current_price=valuation.current_price,
                    rationale=(
                        f"Sell {max_contracts} put(s) at MOS ${target_strike:.2f}; "
                        f"{valuation.margin_of_safety:.0%} below fair value, "
                        f"IV rank {contract.iv_rank if contract.iv_rank is not None else 'n/a'}."
                    ),
                    confidence=0.85 if big_five and big_five.passes_rule_one else 0.65,
                    contracts=max_contracts,
                    total_premium=total_premium,
                    iv_rank=contract.iv_rank,
                    delta=contract.delta,
                    days_to_expiry=contract.days_to_expiry,
                )
                signals.append(signal)

            except Exception as e:
                logger.warning(f"Error analyzing {symbol} for puts: {e}")

        signals.sort(key=lambda x: x.annualized_return, reverse=True)
        return signals

    def find_call_opportunities(self) -> list[RuleOneOptionsSignal]:
        """
        Find opportunities to sell covered calls at Sticker Price.

        "Getting Paid to Sell" strategy:
        - Find stocks you own with >= 100 shares
        - Sell calls at strike near Sticker Price
        - If called away, sell at fair value + premium
        - If not, keep premium and shares

        Returns:
            List of RuleOneOptionsSignal for covered call opportunities
        """
        signals = []

        try:
            positions = self.trader.get_positions()
        except Exception as e:
            logger.error(f"Failed to get positions: {e}")
            return signals

        for pos in positions:
            try:
                symbol = pos.get("symbol")
                qty = float(pos.get("qty", 0))

                if qty < self.min_shares_for_calls:
                    continue

                if symbol not in self.universe:
                    # Only trade options on Rule #1 universe
                    continue

                # Get valuation
                valuation = self._valuation_cache.get(symbol) or self.calculate_sticker_price(
                    symbol
                )
                if not valuation:
                    continue

                target_strike = valuation.sticker_price
                contract = self._find_best_call_option(symbol, target_strike)
                if not contract or contract.mid <= 0:
                    continue

                if contract.iv_rank is not None and contract.iv_rank > self.MAX_IV_RANK:
                    logger.debug(
                        f"{symbol}: Call IV rank {contract.iv_rank:.1f} exceeds max {self.MAX_IV_RANK}"
                    )
                    continue

                if contract.delta is not None and contract.delta > (
                    self.TARGET_DELTA_CALL + self.DELTA_TOLERANCE
                ):
                    logger.debug(
                        f"{symbol}: Call delta {contract.delta:.2f} too high for target {self.TARGET_DELTA_CALL}"
                    )
                    continue

                premium_pct = (
                    contract.mid / valuation.current_price if valuation.current_price else 0
                )
                if premium_pct > self.MAX_PREMIUM_PCT:
                    logger.debug(
                        f"{symbol}: Call premium {premium_pct:.2%} exceeds cap {self.MAX_PREMIUM_PCT:.2%}"
                    )
                    continue

                if contract.days_to_expiry <= 0:
                    continue

                annualized_return = (contract.mid / valuation.current_price) * (
                    365 / contract.days_to_expiry
                )
                if annualized_return < self.MIN_ANNUALIZED_RETURN:
                    continue

                num_contracts = int(qty // 100)
                total_premium = contract.mid * 100 * num_contracts

                signal = RuleOneOptionsSignal(
                    symbol=symbol,
                    signal_type="sell_call",
                    strike=target_strike,
                    expiration=contract.expiration,
                    premium=contract.mid,
                    annualized_return=annualized_return,
                    sticker_price=valuation.sticker_price,
                    mos_price=valuation.mos_price,
                    current_price=valuation.current_price,
                    rationale=(
                        f"Sell {num_contracts} covered call(s) at Sticker ${target_strike:.2f}; "
                        f"IV rank {contract.iv_rank if contract.iv_rank is not None else 'n/a'}."
                    ),
                    confidence=0.9,
                    contracts=num_contracts,
                    total_premium=total_premium,
                    iv_rank=contract.iv_rank,
                    delta=contract.delta,
                    days_to_expiry=contract.days_to_expiry,
                )
                signals.append(signal)

            except Exception as e:
                logger.warning(f"Error analyzing {pos.get('symbol')} for calls: {e}")

        signals.sort(key=lambda x: x.annualized_return, reverse=True)
        return signals

    def _find_best_put_option(self, symbol: str, target_strike: float) -> Optional[OptionContract]:
        """
        Find the best put option near target strike.

        Args:
            symbol: Stock ticker
            target_strike: Desired strike price

        Returns:
            Tuple of (expiration_date, premium) or (None, 0) if not found
        """
        try:
            ticker = yf.Ticker(symbol)
            expirations = ticker.options
            if not expirations:
                return None

            today = datetime.now()
            target_expiry = None
            days_out = 0

            for exp in expirations:
                exp_date = datetime.strptime(exp, "%Y-%m-%d")
                diff_days = (exp_date - today).days
                if self.MIN_DAYS_TO_EXPIRY <= diff_days <= self.MAX_DAYS_TO_EXPIRY:
                    target_expiry = exp
                    days_out = diff_days
                    break

            if not target_expiry:
                target_expiry = expirations[0] if expirations else None
                if target_expiry:
                    exp_date = datetime.strptime(target_expiry, "%Y-%m-%d")
                    days_out = (exp_date - today).days

            if not target_expiry:
                return None

            options = ticker.option_chain(target_expiry)
            puts = options.puts

            if puts.empty:
                return None

            puts = puts.copy()
            puts["strike_diff"] = abs(puts["strike"] - target_strike)
            best_put = puts.loc[puts["strike_diff"].idxmin()]

            bid = float(best_put.get("bid", 0) or 0)
            ask = float(best_put.get("ask", 0) or 0)
            mid = (bid + ask) / 2 if (bid > 0 and ask > 0) else max(bid, ask)
            delta = best_put.get("delta")
            implied_vol = best_put.get("impliedVolatility")
            vol_series = puts["impliedVolatility"] if "impliedVolatility" in puts.columns else []
            iv_rank = self._compute_iv_rank(vol_series, implied_vol)

            return OptionContract(
                symbol=symbol,
                option_type="put",
                expiration=target_expiry,
                strike=float(best_put.get("strike", target_strike)),
                bid=bid,
                ask=ask,
                mid=float(mid or 0),
                delta=float(delta) if delta is not None else None,
                implied_vol=float(implied_vol) if implied_vol is not None else None,
                days_to_expiry=days_out,
                iv_rank=iv_rank,
            )

        except Exception as e:
            logger.debug(f"Could not find put option for {symbol}: {e}")
            return None

    def _find_best_call_option(self, symbol: str, target_strike: float) -> Optional[OptionContract]:
        """
        Find the best call option near target strike.

        Args:
            symbol: Stock ticker
            target_strike: Desired strike price

        Returns:
            Tuple of (expiration_date, premium) or (None, 0) if not found
        """
        try:
            ticker = yf.Ticker(symbol)
            expirations = ticker.options

            if not expirations:
                return None

            today = datetime.now()
            target_expiry = None
            days_out = 0

            for exp in expirations:
                exp_date = datetime.strptime(exp, "%Y-%m-%d")
                diff_days = (exp_date - today).days
                if self.MIN_DAYS_TO_EXPIRY <= diff_days <= self.MAX_DAYS_TO_EXPIRY:
                    target_expiry = exp
                    days_out = diff_days
                    break

            if not target_expiry:
                target_expiry = expirations[0] if expirations else None
                if target_expiry:
                    exp_date = datetime.strptime(target_expiry, "%Y-%m-%d")
                    days_out = (exp_date - today).days

            if not target_expiry:
                return None

            options = ticker.option_chain(target_expiry)
            calls = options.calls

            if calls.empty:
                return None

            calls = calls.copy()
            calls["strike_diff"] = abs(calls["strike"] - target_strike)
            best_call = calls.loc[calls["strike_diff"].idxmin()]

            bid = float(best_call.get("bid", 0) or 0)
            ask = float(best_call.get("ask", 0) or 0)
            mid = (bid + ask) / 2 if (bid > 0 and ask > 0) else max(bid, ask)
            delta = best_call.get("delta")
            implied_vol = best_call.get("impliedVolatility")
            vol_series = calls["impliedVolatility"] if "impliedVolatility" in calls.columns else []
            iv_rank = self._compute_iv_rank(vol_series, implied_vol)

            return OptionContract(
                symbol=symbol,
                option_type="call",
                expiration=target_expiry,
                strike=float(best_call.get("strike", target_strike)),
                bid=bid,
                ask=ask,
                mid=float(mid or 0),
                delta=float(delta) if delta is not None else None,
                implied_vol=float(implied_vol) if implied_vol is not None else None,
                days_to_expiry=days_out,
                iv_rank=iv_rank,
            )

        except Exception as e:
            logger.debug(f"Could not find call option for {symbol}: {e}")
            return None

    def analyze_universe(self) -> dict[str, StickerPriceResult]:
        """
        Analyze all stocks in universe and return valuations.

        Returns:
            Dictionary of symbol -> StickerPriceResult
        """
        results = {}

        for symbol in self.universe:
            self.calculate_big_five(symbol)  # Populates _big_five_cache
            valuation = self.calculate_sticker_price(symbol)

            if valuation:
                results[symbol] = valuation

                logger.info(
                    f"{symbol}: Price=${valuation.current_price:.2f}, "
                    f"Sticker=${valuation.sticker_price:.2f}, "
                    f"MOS=${valuation.mos_price:.2f}, "
                    f"Growth={valuation.growth_rate:.1%}, "
                    f"Rec={valuation.recommendation}"
                )

        return results

    def generate_daily_signals(self) -> dict[str, list[RuleOneOptionsSignal]]:
        """
        Generate all Rule #1 options signals for today.

        Returns:
            Dictionary with 'puts' and 'calls' signal lists
        """
        logger.info("Generating Rule #1 options signals...")

        # First analyze universe to populate valuations
        self.analyze_universe()

        put_signals = self.find_put_opportunities()
        call_signals = self.find_call_opportunities()

        logger.info(
            f"Found {len(put_signals)} put opportunities, {len(call_signals)} call opportunities"
        )

        snapshot = {
            "timestamp": datetime.now().isoformat(),
            "put_opportunities": [self._serialize_signal(s) for s in put_signals],
            "call_opportunities": [self._serialize_signal(s) for s in call_signals],
            "valuations": {
                symbol: self._serialize_valuation(val)
                for symbol, val in self._valuation_cache.items()
            },
            "universe": self.universe,
        }
        self._persist_signals(snapshot)

        return {
            "puts": put_signals,
            "calls": call_signals,
            "timestamp": datetime.now().isoformat(),
        }

    def get_portfolio_analysis(self) -> dict:
        """
        Get comprehensive Rule #1 analysis for current portfolio.

        Returns:
            Dictionary with valuations, signals, and recommendations
        """
        valuations = self.analyze_universe()
        signals = self.generate_daily_signals()

        # Find best opportunities
        best_puts = signals["puts"][:3] if signals["puts"] else []
        best_calls = signals["calls"][:3] if signals["calls"] else []

        # Find undervalued stocks (below MOS)
        undervalued = [v for v in valuations.values() if v.current_price <= v.mos_price]

        # Find overvalued stocks (above Sticker)
        overvalued = [v for v in valuations.values() if v.current_price > v.sticker_price * 1.2]

        return {
            "valuations": {s: v.__dict__ for s, v in valuations.items()},
            "put_opportunities": [s.__dict__ for s in best_puts],
            "call_opportunities": [s.__dict__ for s in best_calls],
            "undervalued_stocks": [v.symbol for v in undervalued],
            "overvalued_stocks": [v.symbol for v in overvalued],
            "universe_size": len(self.universe),
            "analyzed_count": len(valuations),
            "timestamp": datetime.now().isoformat(),
        }


# Example usage
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    strategy = RuleOneOptionsStrategy(paper=True)
    analysis = strategy.get_portfolio_analysis()

    print("\n=== RULE #1 OPTIONS ANALYSIS ===")
    print(f"Analyzed: {analysis['analyzed_count']}/{analysis['universe_size']} stocks")

    print("\n--- Top Put Opportunities (Getting Paid to Wait) ---")
    for opp in analysis["put_opportunities"]:
        print(
            f"  {opp['symbol']}: Sell put at ${opp['strike']:.2f}, "
            f"Yield: {opp['annualized_return']:.1%}, "
            f"Premium ${opp['premium']:.2f}/sh × {opp.get('contracts', 1)} contract(s)"
        )

    print("\n--- Top Call Opportunities (Getting Paid to Sell) ---")
    for opp in analysis["call_opportunities"]:
        print(
            f"  {opp['symbol']}: Sell call at ${opp['strike']:.2f}, "
            f"Yield: {opp['annualized_return']:.1%}, "
            f"Premium ${opp['premium']:.2f}/sh × {opp.get('contracts', 1)} contract(s)"
        )

    print("\n--- Undervalued (Below MOS Price) ---")
    for sym in analysis["undervalued_stocks"]:
        print(f"  {sym}: STRONG BUY")

    print("\n--- Overvalued (Above Sticker Price) ---")
    for sym in analysis["overvalued_stocks"]:
        print(f"  {sym}: Consider selling")
