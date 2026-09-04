"""
Toolset definitions for the cTrader MCP Server.

Each toolset maps to a group of related tools. Only tools listed here
are exposed as MCP tools. New tools are excluded by default — add their
name to the appropriate toolset to include them.

Toolset groups:
  - auth: OAuth authorization flow
  - account: Trader state, cash flow, margin, P/L
  - trading: Orders, positions, deals
  - market_data: Symbols, assets, historical bars/ticks
  - streaming: Live spot, trendbar, depth subscriptions
  - diagnostics: Protocol version, connection status
"""

TOOLSETS: dict[str, dict] = {
    "auth": {
        "tools": [
            "get_authorization_url",
            "exchange_authorization_code",
            "refresh_access_token",
            "get_authorization_status",
        ],
    },
    "account": {
        "tools": [
            "get_trader_info",
            "get_account_assets",
            "get_account_asset_classes",
            "get_cash_flow_history",
            "get_unrealized_pnl",
            "get_margin_call_status",
            "get_expected_margin",
            "get_dynamic_leverage",
        ],
    },
    "trading": {
        "tools": [
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
        ],
    },
    "market_data": {
        "tools": [
            "get_symbols",
            "get_symbol_by_id",
            "get_conversion_symbols",
            "get_trendbars",
            "get_tick_data",
        ],
    },
    "streaming": {
        "tools": [
            "subscribe_spots",
            "unsubscribe_spots",
            "poll_spots",
            "subscribe_trendbars",
            "unsubscribe_trendbars",
            "poll_trendbars",
            "subscribe_depth",
            "unsubscribe_depth",
            "poll_depth",
        ],
    },
    "diagnostics": {
        "tools": [
            "get_protocol_version",
            "get_connection_status",
        ],
    },
}


def get_active_tools(active_toolsets: set[str] | None = None) -> set[str]:
    """Return the set of active tool names.

    Args:
        active_toolsets: Set of toolset names to enable. None means all.

    Returns:
        Set of tool names that should be registered.
    """
    if active_toolsets is None:
        active_toolsets = set(TOOLSETS.keys())

    tools: set[str] = set()
    for ts_name, ts_config in TOOLSETS.items():
        if ts_name in active_toolsets:
            tools.update(ts_config["tools"])
    return tools


def _parse_toolsets() -> set[str] | None:
    """Parse CTRADER_TOOLSETS env var into a set of toolset names.

    Returns None if not set (meaning all toolsets are active).
    """
    import os

    raw = os.environ.get("CTRADER_TOOLSETS", "").strip()
    if not raw:
        return None
    return {t.strip() for t in raw.split(",") if t.strip()}
