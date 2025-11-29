from __future__ import annotations

from typing import Any, Dict, Optional

from mcp.client import MCPClient, default_client

SERVER_ID = "alpaca-trading"


def _client(client: Optional[MCPClient]) -> MCPClient:
    return client or default_client()


def submit_order(
    *,
    symbol: str,
    side: str,
    qty: float,
    order_type: str = "market",
    time_in_force: str = "day",
    extended_hours: bool = False,
    client: Optional[MCPClient] = None,
    **kwargs: Any,
) -> Dict[str, Any]:
    payload = {
        "symbol": symbol,
        "side": side,
        "qty": qty,
        "order_type": order_type,
        "time_in_force": time_in_force,
        "extended_hours": extended_hours,
        **kwargs,
    }
    return _client(client).call_tool(SERVER_ID, "submit_order", payload)


def get_positions(
    *,
    client: Optional[MCPClient] = None,
) -> Dict[str, Any]:
    return _client(client).call_tool(SERVER_ID, "get_positions", {})


def get_clock(
    *,
    client: Optional[MCPClient] = None,
) -> Dict[str, Any]:
    return _client(client).call_tool(SERVER_ID, "get_clock", {})


def get_account(
    *,
    client: Optional[MCPClient] = None,
) -> Dict[str, Any]:
    return _client(client).call_tool(SERVER_ID, "get_account", {})
