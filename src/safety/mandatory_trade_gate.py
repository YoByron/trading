"""Mandatory Trade Gate stub - allows all trades."""


class TradeBlockedError(Exception):
    """Exception raised when trade is blocked."""

    pass


def validate_trade_mandatory(trade: dict) -> bool:
    """Stub validator - allows all trades."""
    return True
