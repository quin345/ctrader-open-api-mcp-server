"""
Tool registry for the cTrader MCP Server.

Maps internal tool identifiers to user-friendly MCP tool names, curated
descriptions, and output risk classifications.

Each key is the canonical tool name. Values contain:
  - name:        the MCP tool name exposed to clients
  - description: curated description shown to LLMs
  - group:       the tool group (auth, account, trading, market_data, streaming, diagnostics)
  - output_risk: classification of untrusted external text in output
"""

from dataclasses import dataclass
from typing import Literal

OutputRisk = Literal["api_structured", "external_text"]


@dataclass(frozen=True, slots=True)
class ToolDefinition:
    name: str
    description: str
    group: str
    output_risk: OutputRisk = "api_structured"


TOOLS: dict[str, ToolDefinition] = {
    # ── Auth ──────────────────────────────────────────────────────────────
    "get_authorization_url": ToolDefinition(
        name="get_authorization_url",
        description=(
            "Returns the cTrader OAuth authorization URL. The user must open "
            "this URL in a browser to authorize the application."
        ),
        group="auth",
    ),
    "exchange_authorization_code": ToolDefinition(
        name="exchange_authorization_code",
        description=(
            "Exchanges an OAuth authorization code for access and refresh tokens."
        ),
        group="auth",
    ),
    "refresh_access_token": ToolDefinition(
        name="refresh_access_token",
        description=(
            "Refreshes the access token using the stored refresh token."
        ),
        group="auth",
    ),
    "get_authorization_status": ToolDefinition(
        name="get_authorization_status",
        description=(
            "Returns the current authorization status including token validity."
        ),
        group="auth",
    ),
    # ── Account ───────────────────────────────────────────────────────────
    "get_trader_info": ToolDefinition(
        name="get_trader_info",
        description=(
            "Retrieves the current trader state for the selected account "
            "including balance, equity, margin, free margin, and leverage."
        ),
        group="account",
    ),
    "get_account_assets": ToolDefinition(
        name="get_account_assets",
        description=(
            "Retrieves the list of assets (currencies) available on the account."
        ),
        group="account",
    ),
    "get_account_asset_classes": ToolDefinition(
        name="get_account_asset_classes",
        description=(
            "Retrieves the list of asset classes available on the account."
        ),
        group="account",
    ),
    "get_cash_flow_history": ToolDefinition(
        name="get_cash_flow_history",
        description=(
            "Retrieves the cash flow history (deposits, withdrawals, bonuses) "
            "for the selected account over a given time range."
        ),
        group="account",
    ),
    "get_unrealized_pnl": ToolDefinition(
        name="get_unrealized_pnl",
        description=(
            "Retrieves the unrealized profit/loss for all open positions."
        ),
        group="account",
    ),
    "get_margin_call_status": ToolDefinition(
        name="get_margin_call_status",
        description=(
            "Retrieves the current margin call status and threshold levels."
        ),
        group="account",
    ),
    "get_expected_margin": ToolDefinition(
        name="get_expected_margin",
        description=(
            "Calculates the expected margin for a hypothetical order."
        ),
        group="account",
    ),
    "get_dynamic_leverage": ToolDefinition(
        name="get_dynamic_leverage",
        description=(
            "Retrieves the dynamic leverage tiers configured for the account."
        ),
        group="account",
    ),
    # ── Trading: Orders ──────────────────────────────────────────────────
    "place_market_order": ToolDefinition(
        name="place_market_order",
        description=(
            "Places a market order on the selected account. Executes "
            "immediately at the current market price."
        ),
        group="trading",
    ),
    "place_limit_order": ToolDefinition(
        name="place_limit_order",
        description=(
            "Places a limit order on the selected account. Executes when "
            "the price reaches the specified limit price."
        ),
        group="trading",
    ),
    "place_stop_order": ToolDefinition(
        name="place_stop_order",
        description=(
            "Places a stop order on the selected account. Executes when "
            "the price reaches the specified stop price."
        ),
        group="trading",
    ),
    "amend_order": ToolDefinition(
        name="amend_order",
        description=(
            "Amends an existing pending order. Can modify limit price, "
            "stop price, and other order parameters."
        ),
        group="trading",
    ),
    "cancel_order": ToolDefinition(
        name="cancel_order",
        description=(
            "Cancels an existing pending order on the selected account."
        ),
        group="trading",
    ),
    "get_orders": ToolDefinition(
        name="get_orders",
        description=(
            "Retrieves the list of pending orders on the selected account."
        ),
        group="trading",
    ),
    "get_order_by_id": ToolDefinition(
        name="get_order_by_id",
        description=(
            "Retrieves a single order by its ID on the selected account."
        ),
        group="trading",
    ),

    # ── Trading: Positions ───────────────────────────────────────────────
    "get_positions": ToolDefinition(
        name="get_positions",
        description=(
            "Retrieves all open positions on the selected account."
        ),
        group="trading",
    ),
    "get_position_by_id": ToolDefinition(
        name="get_position_by_id",
        description=(
            "Retrieves a single open position by its ID."
        ),
        group="trading",
    ),
    "close_position": ToolDefinition(
        name="close_position",
        description=(
            "Closes an open position on the selected account. "
            "Optionally specify a partial volume for partial close."
        ),
        group="trading",
    ),
    "close_all_positions": ToolDefinition(
        name="close_all_positions",
        description=(
            "Closes all open positions on the selected account."
        ),
        group="trading",
    ),
    "get_deals": ToolDefinition(
        name="get_deals",
        description=(
            "Retrieves the list of executed deals (fills) on the selected "
            "account over a given time range."
        ),
        group="trading",
    ),
    "get_deals_by_position": ToolDefinition(
        name="get_deals_by_position",
        description=(
            "Retrieves the deals (fills) associated with a specific position."
        ),
        group="trading",
    ),
    # ── Market Data: Symbols & Assets ────────────────────────────────────
    "get_symbols": ToolDefinition(
        name="get_symbols",
        description=(
            "Retrieves the list of tradable symbols available on the account."
        ),
        group="market_data",
    ),
    "get_symbol_by_id": ToolDefinition(
        name="get_symbol_by_id",
        description=(
            "Retrieves detailed metadata for a specific symbol by its ID."
        ),
        group="market_data",
    ),
    "get_conversion_symbols": ToolDefinition(
        name="get_conversion_symbols",
        description=(
            "Retrieves the list of symbol pairs available for currency conversion."
        ),
        group="market_data",
    ),
    "get_trendbars": ToolDefinition(
        name="get_trendbars",
        description=(
            "Retrieves historical trendbars (OHLC bars) for a symbol. "
            "Supports relative lookback and absolute time ranges."
        ),
        group="market_data",
    ),
    "get_tick_data": ToolDefinition(
        name="get_tick_data",
        description=(
            "Retrieves historical tick-level price data for a symbol."
        ),
        group="market_data",
    ),
    # ── Streaming ─────────────────────────────────────────────────────────
    "subscribe_spots": ToolDefinition(
        name="subscribe_spots",
        description=(
            "Subscribes to live spot price updates for one or more symbols."
        ),
        group="streaming",
    ),
    "unsubscribe_spots": ToolDefinition(
        name="unsubscribe_spots",
        description=(
            "Unsubscribes from live spot price updates for one or more symbols."
        ),
        group="streaming",
    ),
    "poll_spots": ToolDefinition(
        name="poll_spots",
        description=(
            "Retrieves buffered live spot price events since the last poll. "
            "Non-blocking: returns immediately with available events."
        ),
        group="streaming",
    ),
    "subscribe_trendbars": ToolDefinition(
        name="subscribe_trendbars",
        description=(
            "Subscribes to live trendbar updates for a symbol and timeframe."
        ),
        group="streaming",
    ),
    "unsubscribe_trendbars": ToolDefinition(
        name="unsubscribe_trendbars",
        description=(
            "Unsubscribes from live trendbar updates for a symbol."
        ),
        group="streaming",
    ),
    "poll_trendbars": ToolDefinition(
        name="poll_trendbars",
        description=(
            "Retrieves buffered live trendbar events since the last poll."
        ),
        group="streaming",
    ),
    "subscribe_depth": ToolDefinition(
        name="subscribe_depth",
        description=(
            "Subscribes to live market depth (order book) updates for symbols."
        ),
        group="streaming",
    ),
    "unsubscribe_depth": ToolDefinition(
        name="unsubscribe_depth",
        description=(
            "Unsubscribes from live market depth updates for symbols."
        ),
        group="streaming",
    ),
    "poll_depth": ToolDefinition(
        name="poll_depth",
        description=(
            "Retrieves buffered market depth events since the last poll."
        ),
        group="streaming",
    ),
    # ── Diagnostics ──────────────────────────────────────────────────────
    "get_protocol_version": ToolDefinition(
        name="get_protocol_version",
        description=(
            "Retrieves the cTrader Open API protocol version."
        ),
        group="diagnostics",
    ),
    "get_connection_status": ToolDefinition(
        name="get_connection_status",
        description=(
            "Returns the current connection and authentication status."
        ),
        group="diagnostics",
    ),
}

# Derived lookups used by server.py and security.py
TOOL_NAMES: dict[str, str] = {key: t.name for key, t in TOOLS.items()}
TOOL_DESCRIPTIONS: dict[str, str] = {key: t.description for key, t in TOOLS.items()}
TOOL_GROUPS: dict[str, str] = {key: t.group for key, t in TOOLS.items()}
TOOL_OUTPUT_RISK_BY_NAME: dict[str, OutputRisk] = {
    t.name: t.output_risk for t in TOOLS.values()
}

# Group-to-tools mapping
TOOLS_BY_GROUP: dict[str, list[str]] = {}
for key, t in TOOLS.items():
    TOOLS_BY_GROUP.setdefault(t.group, []).append(t.name)
