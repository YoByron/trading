"""
Market data utilities with resilient fetching across free sources.

Primary source: Yahoo Finance via yfinance (with hardened session headers)
Fallback source: Alpha Vantage Daily Adjusted (free tier, throttled).

Designed to keep the trading workflows running on zero-cost data plans.
"""

from __future__ import annotations

import logging
import os
import time
from datetime import datetime, timedelta
from typing import Optional

import pandas as pd
import requests
import yfinance as yf

logger = logging.getLogger(__name__)


class MarketDataProvider:
    """Fetch daily OHLCV data with retries and multi-source fallbacks."""

    YFINANCE_LOOKBACK_BUFFER_DAYS = 5
    ALPHAVANTAGE_MIN_INTERVAL_SECONDS = 15  # Free tier: 5 calls/minute

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

        data = self._fetch_yfinance(symbol, start_dt, end_dt)
        if self._is_valid(data, lookback_days):
            return self._prepare(data, lookback_days)

        logger.warning(
            "%s: yfinance returned insufficient data (%s rows). Falling back to Alpha Vantage.",
            symbol,
            len(data) if data is not None else 0,
        )

        data = self._fetch_alpha_vantage(symbol)
        if self._is_valid(data, lookback_days):
            return self._prepare(data, lookback_days)

        raise ValueError(
            f"Failed to fetch {lookback_days} days of data for {symbol} "
            "from both yfinance and Alpha Vantage."
        )

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _fetch_yfinance(
        self, symbol: str, start_dt: datetime, end_dt: datetime
    ) -> Optional[pd.DataFrame]:
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
        except Exception as exc:
            logger.warning("yfinance fetch failed for %s: %s", symbol, exc)
        return None

    def _fetch_alpha_vantage(self, symbol: str) -> Optional[pd.DataFrame]:
        if not self.alpha_vantage_key:
            logger.warning(
                "%s: Alpha Vantage fallback unavailable (missing API key).", symbol
            )
            return None

        # Throttle to respect free-tier rate limits
        elapsed = time.time() - self._last_alpha_call_ts
        if elapsed < self.ALPHAVANTAGE_MIN_INTERVAL_SECONDS:
            sleep_time = self.ALPHAVANTAGE_MIN_INTERVAL_SECONDS - elapsed
            time.sleep(sleep_time)

        params = {
            "function": "TIME_SERIES_DAILY_ADJUSTED",
            "symbol": symbol,
            "outputsize": "compact",
            "apikey": self.alpha_vantage_key,
        }

        try:
            response = self.session.get(
                "https://www.alphavantage.co/query", params=params, timeout=30
            )
            self._last_alpha_call_ts = time.time()
            response.raise_for_status()
            payload = response.json()
        except Exception as exc:
            logger.warning("Alpha Vantage request failed for %s: %s", symbol, exc)
            return None

        time_series = payload.get("Time Series (Daily)")
        if not time_series:
            logger.warning(
                "%s: Alpha Vantage response missing time series (payload keys: %s)",
                symbol,
                list(payload.keys()),
            )
            return None

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

        if not records:
            return None

        df = pd.DataFrame(records).set_index("Date").sort_index()
        return df

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


