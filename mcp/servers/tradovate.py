from __future__ import annotations

from typing import Any, Dict, Optional

from mcp.client import MCPClient, default_client

SERVER_ID = "tradovate"


def _client(client: Optional[MCPClient]) -> MCPClient:
    return client or default_client()


def place_order(
    *,
    contract: str,
    side: str,
    quantity: int,
    order_type: str = "market",
    client: Optional[MCPClient] = None,
    **kwargs: Any,
) -> Dict[str, Any]:
    payload = {
        "contract": contract,
        "side": side,
        "quantity": quantity,
        "order_type": order_type,
        **kwargs,
    }
    return _client(client).call_tool(SERVER_ID, "place_order", payload)


def get_positions(
    *,
    client: Optional[MCPClient] = None,
) -> Dict[str, Any]:
    return _client(client).call_tool(SERVER_ID, "get_positions", {})


def get_contract_details(
    *,
    contract: str,
    client: Optional[MCPClient] = None,
) -> Dict[str, Any]:
    payload = {"contract": contract}
    return _client(client).call_tool(SERVER_ID, "get_contract_details", payload)

