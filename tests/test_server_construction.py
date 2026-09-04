"""
Layer 1: Server construction tests — no network, no real credentials.

Verifies that build_server() produces the expected set of MCP tools.
Catches FastMCP API breakage and tool configuration errors.
"""

from __future__ import annotations

import os
from unittest.mock import patch

import pytest
from fastmcp.client import Client

from ctrader_mcp_server.security import DATA_KEY, SECURITY_KEY
from ctrader_mcp_server.server import build_server

DUMMY_ENV = {
    "CTRADER_CLIENT_ID": "test-key",
    "CTRADER_CLIENT_SECRET": "test-secret",
    "CTRADER_ENVIRONMENT": "demo",
    "CTRADER_ACCOUNT_ID": "12345",
}

EXPECTED_TOOLS = {
    # Auth
    "get_authorization_url",
    "exchange_authorization_code",
    "refresh_access_token",
    "get_authorization_status",
    # Account
    "get_trader_info",
    "get_account_assets",
    "get_account_asset_classes",
    "get_cash_flow_history",
    "get_unrealized_pnl",
    "get_margin_call_status",
    "get_expected_margin",
    "get_dynamic_leverage",
    # Trading
    "place_market_order",
    "place_limit_order",
    "place_stop_order",
    "amend_order",
    "cancel_order",
    "get_orders",
    "get_order_by_id",
    "get_positions",
    "get_position_by_id",
    "close_position",
    "close_all_positions",
    "get_deals",
    "get_deals_by_position",
    # Market Data
    "get_symbols",
    "get_symbol_by_id",
    "get_conversion_symbols",
    "get_trendbars",
    "get_tick_data",
    # Streaming
    "subscribe_spots",
    "unsubscribe_spots",
    "poll_spots",
    "subscribe_trendbars",
    "unsubscribe_trendbars",
    "poll_trendbars",
    "subscribe_depth",
    "unsubscribe_depth",
    "poll_depth",
    # Diagnostics
    "get_protocol_version",
    "get_connection_status",
}


async def _list_tools(env: dict[str, str] | None = None) -> list:
    """Build the server and list its tools."""
    merged = {**DUMMY_ENV, **(env or {})}
    with patch.dict(os.environ, merged, clear=False):
        server = build_server()
    async with Client(transport=server) as client:
        return await client.list_tools()


@pytest.mark.asyncio
async def test_all_expected_tools_present():
    """All expected tools should be present in the default configuration."""
    tools = await _list_tools()
    names = {t.name for t in tools}
    missing = EXPECTED_TOOLS - names
    assert not missing, f"Missing tools: {missing}"


@pytest.mark.asyncio
async def test_toolset_filtering():
    """CTRADER_TOOLSETS should limit which tools are exposed."""
    tools = await _list_tools({"CTRADER_TOOLSETS": "auth"})
    names = {t.name for t in tools}
    assert "get_authorization_url" in names
    assert "place_market_order" not in names
    assert "get_symbols" not in names


@pytest.mark.asyncio
async def test_tools_have_descriptions():
    """Every tool must have a non-empty description."""
    tools = await _list_tools()
    for t in tools:
        assert t.description, f"{t.name} missing description"
        assert len(t.description.strip()) > 10, (
            f"{t.name} description too short"
        )


@pytest.mark.asyncio
async def test_order_tools_have_destructive_hint():
    """Order placement tools must be annotated as destructive."""
    tools = await _list_tools()
    order_tools = [t for t in tools if t.name.startswith("place_")]
    assert len(order_tools) == 3
    for t in order_tools:
        annotations = t.annotations
        assert annotations is not None, f"{t.name} missing annotations"
        assert annotations.destructiveHint is True, (
            f"{t.name} should have destructiveHint=True"
        )


@pytest.mark.asyncio
async def test_read_only_tools_have_readonly_hint():
    """Read-only query tools should have readOnlyHint=True."""
    tools = await _list_tools()
    read_only_tools = [t for t in tools if t.name.startswith("get_")]
    for t in read_only_tools:
        annotations = t.annotations
        assert annotations is not None, f"{t.name} missing annotations"
        assert annotations.readOnlyHint is True, (
            f"{t.name} should have readOnlyHint=True"
        )
