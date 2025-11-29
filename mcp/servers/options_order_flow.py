from __future__ import annotations

from typing import Any, Dict, Optional

from mcp.client import MCPClient, default_client

SERVER_ID = "options-order-flow"


def _client(client: Optional[MCPClient]) -> MCPClient:
    return client or default_client()


def live_summary(
    *,
    symbols: Optional[list[str]] = None,
    min_notional: Optional[float] = None,
    client: Optional[MCPClient] = None,
) -> Dict[str, Any]:
    payload: Dict[str, Any] = {}
    if symbols:
        payload["symbols"] = symbols
    if min_notional is not None:
        payload["min_notional"] = min_notional
    return _client(client).call_tool(SERVER_ID, "live_summary", payload)


def unusual_activity(
    *,
    symbol: str,
    lookback_minutes: int = 30,
    client: Optional[MCPClient] = None,
) -> Dict[str, Any]:
    payload = {
        "symbol": symbol,
        "lookback_minutes": lookback_minutes,
    }
    return _client(client).call_tool(SERVER_ID, "unusual_activity", payload)


def flow_snapshot(
    *,
    symbol: str,
    client: Optional[MCPClient] = None,
) -> Dict[str, Any]:
    payload = {"symbol": symbol}
    return _client(client).call_tool(SERVER_ID, "flow_snapshot", payload)
