from __future__ import annotations

from typing import Any, Dict, Optional

from mcp.client import MCPClient, default_client

SERVER_ID = "metatrader"


def _client(client: Optional[MCPClient]) -> MCPClient:
    return client or default_client()


def place_order(
    *,
    symbol: str,
    side: str,
    volume: float,
    order_type: str = "market",
    deviation: Optional[int] = None,
    client: Optional[MCPClient] = None,
    **kwargs: Any,
) -> Dict[str, Any]:
    payload = {
        "symbol": symbol,
        "side": side,
        "volume": volume,
        "order_type": order_type,
        **kwargs,
    }
    if deviation is not None:
        payload["deviation"] = deviation
    return _client(client).call_tool(SERVER_ID, "place_order", payload)


def get_open_positions(
    *,
    client: Optional[MCPClient] = None,
) -> Dict[str, Any]:
    return _client(client).call_tool(SERVER_ID, "get_open_positions", {})


def get_indicator(
    *,
    symbol: str,
    indicator: str,
    timeframe: str = "H1",
    period: Optional[int] = None,
    client: Optional[MCPClient] = None,
) -> Dict[str, Any]:
    payload: Dict[str, Any] = {
        "symbol": symbol,
        "indicator": indicator,
        "timeframe": timeframe,
    }
    if period is not None:
        payload["period"] = period
    return _client(client).call_tool(SERVER_ID, "get_indicator", payload)
