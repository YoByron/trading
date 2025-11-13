"""
Market data utilities with resilient fetching across multiple sources.

Priority order:
1. Yahoo Finance via yfinance (with hardened session headers)
2. Alpaca API (if credentials available - preferred fallback)
3. Alpha Vantage Daily Adjusted (free tier, throttled - last resort)

Designed to keep the trading workflows running on zero-cost data plans.
"""

from __future__ import annotations

import logging
import os
import random
import time
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Dict, Optional, Tuple

import pandas as pd
import requests
import yfinance as yf

logger = logging.getLogger(__name__)


class MarketDataProvider:
    """Fetch daily OHLCV data with retries and multi-source fallbacks."""

    YFINANCE_LOOKBACK_BUFFER_DAYS = 5
    YFINANCE_SECONDARY_LOOKBACK_DAYS = 120
    ALPHAVANTAGE_MIN_INTERVAL_SECONDS = 15  # Free tier: 5 calls/minute
    ALPHAVANTAGE_BACKOFF_SECONDS = 60
    ALPHAVANTAGE_MAX_RETRIES = 4
    CACHE_TTL_SECONDS = 6 * 60 * 60  # 6 hours

    def __init__(
        self,
        alpha_vantage_key: Optional[str] = None,
        session: Optional[requests.Session] = None,
    ) -> None:
        self.session = session or requests.Session()
        # Harden yfinance requests to reduce 403/429 responses
        self.session.headers.update(
            {
                "User-Agent": (
                    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/119.0.0.0 Safari/537.36"
                ),
                "Accept": "application/json,text/html;q=0.9,*/*;q=0.8",
            }
        )
        self.alpha_vantage_key = alpha_vantage_key or os.getenv(
            "ALPHA_VANTAGE_API_KEY"
        )
        self._last_alpha_call_ts: float = 0.0
        self._cache: Dict[Tuple[str, int, date], pd.DataFrame] = {}
        cache_root = os.getenv("MARKET_DATA_CACHE_DIR", "data/cache/alpha_vantage")
        self.cache_dir = Path(cache_root)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize Alpaca API if credentials available
        self._alpaca_api = None
        alpaca_key = os.getenv("ALPACA_API_KEY")
        alpaca_secret = os.getenv("ALPACA_SECRET_KEY")
        if alpaca_key and alpaca_secret:
            try:
                import alpaca_trade_api as tradeapi
                self._alpaca_api = tradeapi.REST(
                    key_id=alpaca_key,
                    secret_key=alpaca_secret,
                    base_url=os.getenv("APCA_API_BASE_URL", "https://paper-api.alpaca.markets"),
                    api_version="v2",
                )
                logger.info("Alpaca API initialized for market data fallback")
            except Exception as e:
                logger.warning(f"Failed to initialize Alpaca API for market data: {e}")
                self._alpaca_api = None

    def get_daily_bars(
        self,
        symbol: str,
        lookback_days: int,
        end_datetime: Optional[datetime] = None,
    ) -> pd.DataFrame:
        """
        Retrieve daily OHLCV candles for a symbol.

        Args:
            symbol: Equity ticker symbol.
            lookback_days: Number of trading days required (excludes buffer).
            end_datetime: Optional custom end date (defaults to now).

        Returns:
            pandas.DataFrame with columns [Open, High, Low, Close, Volume]
            indexed by pandas.DatetimeIndex.

        Raises:
            ValueError: if data cannot be fetched from either source.
        """
        end_dt = end_datetime or datetime.now()
        start_dt = end_dt - timedelta(
            days=lookback_days + self.YFINANCE_LOOKBACK_BUFFER_DAYS
        )
        cache_key = (symbol.upper(), lookback_days, end_dt.date())
        cached = self._cache.get(cache_key)
        if cached is not None and not cached.empty:
            return cached.copy()

        data = self._fetch_yfinance(symbol, start_dt, end_dt)
        if self._is_valid(data, lookback_days):
            prepared = self._prepare(data, lookback_days)
            self._cache[cache_key] = prepared
            return prepared.copy()

        logger.warning(
            "%s: yfinance returned insufficient data (%s rows). Trying Alpaca API fallback.",
            symbol,
            len(data) if data is not None else 0,
        )

        # Try Alpaca API first (faster, more reliable than Alpha Vantage)
        data = self._fetch_alpaca(symbol, lookback_days)
        if self._is_valid(data, lookback_days):
            prepared = self._prepare(data, lookback_days)
            self._cache[cache_key] = prepared
            return prepared.copy()

        # Last resort: Alpha Vantage (slow, rate-limited)
        logger.warning(
            "%s: Alpaca API failed. Falling back to Alpha Vantage (may be slow).",
            symbol,
        )
        data = self._fetch_alpha_vantage(symbol)
        if self._is_valid(data, lookback_days):
            prepared = self._prepare(data, lookback_days)
            self._cache[cache_key] = prepared
            return prepared.copy()

        raise ValueError(
            f"Failed to fetch {lookback_days} days of data for {symbol} "
            "from yfinance, Alpaca API, and Alpha Vantage."
        )

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _fetch_yfinance(
        self, symbol: str, start_dt: datetime, end_dt: datetime
    ) -> Optional[pd.DataFrame]:
        sleep_seconds = random.uniform(0.3, 1.2)
        time.sleep(sleep_seconds)
        try:
            data = yf.download(
                symbol,
                start=start_dt,
                end=end_dt,
                progress=False,
                session=self.session,
                auto_adjust=False,
                threads=False,
            )
            if isinstance(data, pd.DataFrame) and not data.empty:
                return data
            logger.debug("%s: yfinance primary download returned empty frame.", symbol)
        except Exception as exc:
            logger.warning("yfinance fetch failed for %s: %s", symbol, exc)

        # Secondary attempt using Ticker.history (sometimes succeeds when download fails)
        try:
            ticker = yf.Ticker(symbol, session=self.session)
            history = ticker.history(
                start=start_dt.strftime("%Y-%m-%d"),
                end=end_dt.strftime("%Y-%m-%d"),
                interval="1d",
                auto_adjust=False,
            )
            if isinstance(history, pd.DataFrame) and not history.empty:
                return history
        except Exception as exc:
            logger.debug("%s: yfinance ticker.history failed: %s", symbol, exc)

        # Final attempt: broader lookback to mitigate sparse weekends/holidays
        try:
            extended_start = end_dt - timedelta(days=self.YFINANCE_SECONDARY_LOOKBACK_DAYS)
            extended = yf.download(
                symbol,
                start=extended_start,
                end=end_dt,
                progress=False,
                session=self.session,
                auto_adjust=False,
                threads=False,
            )
            if isinstance(extended, pd.DataFrame) and not extended.empty:
                return extended
        except Exception as exc:
            logger.debug("%s: yfinance extended download failed: %s", symbol, exc)

        return None

    def _fetch_alpaca(self, symbol: str, lookback_days: int) -> Optional[pd.DataFrame]:
        """Fetch market data from Alpaca API (preferred fallback)."""
        if not self._alpaca_api:
            logger.debug("%s: Alpaca API not available (missing credentials)", symbol)
            return None

        try:
            # Alpaca API: get_bars returns BarSet, convert to DataFrame
            barset = self._alpaca_api.get_bars(
                symbol,
                "1Day",
                limit=lookback_days + self.YFINANCE_LOOKBACK_BUFFER_DAYS,
            )
            
            if not barset or len(barset) == 0:
                logger.warning("%s: Alpaca API returned no bars", symbol)
                return None

            # Convert Alpaca bars to pandas DataFrame
            records = []
            for bar in barset:
                records.append(
                    {
                        "Open": float(bar.o),
                        "High": float(bar.h),
                        "Low": float(bar.l),
                        "Close": float(bar.c),
                        "Volume": int(bar.v),
                    }
                )
            
            if not records:
                return None

            # Create DataFrame with datetime index
            df = pd.DataFrame(records, index=[bar.t for bar in barset])
            df.index.name = "Date"
            df = df.sort_index()
            
            logger.info("%s: Successfully fetched %d bars from Alpaca API", symbol, len(df))
            return df

        except Exception as exc:
            logger.warning("%s: Alpaca API fetch failed: %s", symbol, exc)
            return None

    def _fetch_alpha_vantage(self, symbol: str) -> Optional[pd.DataFrame]:
        if not self.alpha_vantage_key:
            logger.warning(
                "%s: Alpha Vantage fallback unavailable (missing API key).", symbol
            )
            return None

        cache_file = self.cache_dir / f"{symbol.upper()}_{datetime.utcnow().date()}.csv"
        if cache_file.exists():
            age = time.time() - cache_file.stat().st_mtime
            if age <= self.CACHE_TTL_SECONDS:
                try:
                    cached_df = pd.read_csv(cache_file, parse_dates=["Date"], index_col="Date")
                    if not cached_df.empty:
                        return cached_df
                except Exception as exc:
                    logger.debug("%s: Failed to load cached Alpha Vantage data: %s", symbol, exc)

        # Throttle to respect free-tier rate limits
        def respect_rate_limit(min_interval: float) -> None:
            elapsed = time.time() - self._last_alpha_call_ts
            if elapsed < min_interval:
                sleep_time = min_interval - elapsed
                logger.debug("Sleeping %.2fs to respect Alpha Vantage rate limit", sleep_time)
                time.sleep(sleep_time)

        params = {
            "function": "TIME_SERIES_DAILY_ADJUSTED",
            "symbol": symbol,
            "outputsize": "compact",
            "datatype": "json",
            "apikey": self.alpha_vantage_key,
        }

        for attempt in range(1, self.ALPHAVANTAGE_MAX_RETRIES + 1):
            respect_rate_limit(self.ALPHAVANTAGE_MIN_INTERVAL_SECONDS)
            try:
                response = self.session.get(
                    "https://www.alphavantage.co/query", params=params, timeout=30
                )
                self._last_alpha_call_ts = time.time()
                response.raise_for_status()
                payload = response.json()
            except Exception as exc:
                logger.warning("Alpha Vantage request failed for %s (attempt %s): %s", symbol, attempt, exc)
                continue

            time_series = payload.get("Time Series (Daily)")
            if time_series:
                records = []
                for date_str, values in time_series.items():
                    try:
                        records.append(
                            {
                                "Date": datetime.strptime(date_str, "%Y-%m-%d"),
                                "Open": float(values["1. open"]),
                                "High": float(values["2. high"]),
                                "Low": float(values["3. low"]),
                                "Close": float(values["4. close"]),
                                "Volume": float(values["6. volume"]),
                            }
                        )
                    except Exception as exc:
                        logger.debug(
                            "%s: Skipping Alpha Vantage row %s (%s)", symbol, date_str, exc
                        )

                if records:
                    df = pd.DataFrame(records).set_index("Date").sort_index()
                    try:
                        df.to_csv(cache_file, index=True)
                    except Exception as exc:
                        logger.debug("%s: Unable to cache Alpha Vantage data: %s", symbol, exc)
                    return df

            # Handle throttling notices
            info_message = payload.get("Information") or payload.get("Note")
            if info_message:
                backoff = self.ALPHAVANTAGE_BACKOFF_SECONDS * attempt
                logger.warning(
                    "%s: Alpha Vantage rate limit hit (attempt %s). Backing off for %ss. Message: %s",
                    symbol,
                    attempt,
                    backoff,
                    info_message,
                )
                time.sleep(backoff)
                continue

            logger.warning(
                "%s: Alpha Vantage response missing time series (keys: %s)",
                symbol,
                list(payload.keys()),
            )
            time.sleep(self.ALPHAVANTAGE_BACKOFF_SECONDS * attempt)

        return None

    @staticmethod
    def _is_valid(data: Optional[pd.DataFrame], lookback_days: int) -> bool:
        if data is None or data.empty:
            return False
        return len(data.index.unique()) >= lookback_days

    @staticmethod
    def _prepare(data: pd.DataFrame, lookback_days: int) -> pd.DataFrame:
        df = (
            data.copy()
            .rename(
                columns={
                    "Adj Close": "Adj Close",
                    "Open": "Open",
                    "High": "High",
                    "Low": "Low",
                    "Close": "Close",
                    "Volume": "Volume",
                }
            )
        )
        # Ensure index is datetime and unique
        if not isinstance(df.index, pd.DatetimeIndex):
            df.index = pd.to_datetime(df.index)
        df = df[~df.index.duplicated(keep="last")].sort_index()
        return df.tail(lookback_days)


def get_market_data_provider() -> MarketDataProvider:
    """Convenience singleton-style accessor."""
    if not hasattr(get_market_data_provider, "_instance"):
        get_market_data_provider._instance = MarketDataProvider()  # type: ignore[attr-defined]
    return get_market_data_provider._instance  # type: ignore[attr-defined]


