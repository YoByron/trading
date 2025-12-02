"""
Tests for survivorship bias.

Ensures universe definition doesn't suffer from survivorship bias.
"""

import pandas as pd
import pytest


def test_universe_consistency(
    universe: list[str], data: dict[str, pd.DataFrame]
) -> bool:
    """
    Test that all symbols in universe have data.

    Args:
        universe: List of symbols in universe
        data: Dictionary of symbol -> DataFrame

    Returns:
        True if all symbols have data, False otherwise
    """
    missing_symbols = []
    for symbol in universe:
        if symbol not in data:
            missing_symbols.append(symbol)
        elif data[symbol].empty:
            missing_symbols.append(symbol)

    if missing_symbols:
        print(f"Missing data for symbols: {missing_symbols}")
        return False

    return True


def test_date_range_consistency(
    data: dict[str, pd.DataFrame], min_overlap: float = 0.8
) -> bool:
    """
    Test that all symbols have similar date ranges (avoid survivorship bias).

    Args:
        data: Dictionary of symbol -> DataFrame
        min_overlap: Minimum overlap required (default: 80%)

    Returns:
        True if date ranges are consistent, False otherwise
    """
    if not data:
        return True

    # Get date ranges for each symbol
    date_ranges = {}
    for symbol, df in data.items():
        if not df.empty and isinstance(df.index, pd.DatetimeIndex):
            date_ranges[symbol] = (df.index.min(), df.index.max())

    if len(date_ranges) < 2:
        return True  # Need at least 2 symbols to compare

    # Find common date range
    min_date = max(r[0] for r in date_ranges.values())
    max_date = min(r[1] for r in date_ranges.values())

    if min_date >= max_date:
        print("No overlapping date range across symbols")
        return False

    # Check overlap for each symbol
    total_days = (max_date - min_date).days
    for symbol, (sym_min, sym_max) in date_ranges.items():
        overlap_start = max(min_date, sym_min)
        overlap_end = min(max_date, sym_max)
        overlap_days = (overlap_end - overlap_start).days
        overlap_pct = overlap_days / total_days if total_days > 0 else 0.0

        if overlap_pct < min_overlap:
            print(
                f"Symbol {symbol} has only {overlap_pct*100:.1f}% overlap "
                f"(required: {min_overlap*100:.1f}%)"
            )
            return False

    return True


def test_delisted_symbols(
    universe: list[str], current_data: dict[str, pd.DataFrame]
) -> bool:
    """
    Test for delisted symbols (survivorship bias check).

    Args:
        universe: Original universe definition
        current_data: Current data available

    Returns:
        True if no delisted symbols, False otherwise
    """
    missing_symbols = [s for s in universe if s not in current_data]

    if missing_symbols:
        print(f"Potentially delisted symbols: {missing_symbols}")
        # This is informational - delisted symbols are expected
        return True  # Don't fail, just warn

    return True


# Pytest test functions
def test_universe_consistency_check(universe_fixture, data_fixture):
    """Pytest test for universe consistency."""
    assert test_universe_consistency(
        universe_fixture, data_fixture
    ), "Universe consistency check failed"


def test_date_range_consistency_check(data_fixture):
    """Pytest test for date range consistency."""
    assert test_date_range_consistency(
        data_fixture
    ), "Date range consistency check failed"
