"""
Tests for timezone consistency.

Ensures all data uses consistent timezones.
"""

import pandas as pd


def test_timezone_consistency(data: pd.DataFrame, expected_tz: str = "UTC") -> bool:
    """
    Test that all timestamps use consistent timezone.

    Args:
        data: DataFrame with datetime index
        expected_tz: Expected timezone (default: UTC)

    Returns:
        True if timezone is consistent, False otherwise
    """
    if not isinstance(data.index, pd.DatetimeIndex):
        raise ValueError("Data must have DatetimeIndex")

    # Check if index is timezone-aware
    if data.index.tz is None:
        print("Data index is timezone-naive")
        return False

    # Check if timezone matches expected
    if str(data.index.tz) != expected_tz:
        print(f"Expected timezone: {expected_tz}, got: {data.index.tz}")
        return False

    return True


def test_no_timezone_mixing(data: dict[str, pd.DataFrame]) -> bool:
    """
    Test that all symbols use the same timezone.

    Args:
        data: Dictionary of symbol -> DataFrame

    Returns:
        True if all timezones are consistent, False otherwise
    """
    if not data:
        return True

    timezones = {}
    for symbol, df in data.items():
        if isinstance(df.index, pd.DatetimeIndex):
            tz = str(df.index.tz) if df.index.tz else "naive"
            timezones[symbol] = tz

    unique_timezones = set(timezones.values())
    if len(unique_timezones) > 1:
        print(f"Found mixed timezones: {unique_timezones}")
        for symbol, tz in timezones.items():
            print(f"  {symbol}: {tz}")
        return False

    return True


# Pytest test functions
def test_timezone_consistency_check(data_fixture):
    """Pytest test for timezone consistency."""
    assert test_timezone_consistency(data_fixture, expected_tz="UTC"), (
        "Timezone consistency check failed"
    )


def test_no_timezone_mixing_check(data_fixture):
    """Pytest test for timezone mixing."""
    assert test_no_timezone_mixing(data_fixture), "Found mixed timezones across symbols"
