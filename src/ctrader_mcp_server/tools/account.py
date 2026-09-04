"""
Account tools for the cTrader MCP Server.

Provides trader state, cash flow, margin, P/L, and related account queries.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from fastmcp import FastMCP
    from ..session import CTraderSession


def register_account_tools(server: FastMCP, session: CTraderSession) -> None:
    """Register account tools on the given server."""

    @server.tool(
        description=(
            "Retrieves the current trader state for the selected account "
            "including balance, equity, margin, free margin, and leverage."
        ),
        annotations={
            "title": "Get Trader Info",
            "readOnlyHint": True,
            "openWorldHint": True,
        },
    )
    async def get_trader_info() -> dict:
        """Get trader information."""
        try:
            return await session.get_trader_info()
        except Exception as exc:
            return {"error": {"message": f"Failed to get trader info: {exc}"}}

    @server.tool(
        description=(
            "Retrieves the list of assets (currencies) available on the account."
        ),
        annotations={
            "title": "Get Account Assets",
            "readOnlyHint": True,
            "openWorldHint": True,
        },
    )
    async def get_account_assets() -> dict:
        """Get account assets."""
        try:
            return {"assets": [], "note": "Asset list not yet implemented"}
        except Exception as exc:
            return {"error": {"message": f"Failed to get assets: {exc}"}}

    @server.tool(
        description=(
            "Retrieves the list of asset classes available on the account."
        ),
        annotations={
            "title": "Get Account Asset Classes",
            "readOnlyHint": True,
            "openWorldHint": True,
        },
    )
    async def get_account_asset_classes() -> dict:
        """Get account asset classes."""
        try:
            return {"assetClasses": [], "note": "Not yet implemented"}
        except Exception as exc:
            return {"error": {"message": f"Failed to get asset classes: {exc}"}}


    @server.tool(
        description=(
            "Retrieves the unrealized profit/loss for all open positions."
        ),
        annotations={
            "title": "Get Unrealized PnL",
            "readOnlyHint": True,
            "openWorldHint": True,
        },
    )
    async def get_unrealized_pnl() -> dict:
        """Get unrealized P/L."""
        try:
            positions = await session.get_positions()
            total_pnl = sum(p.get("unrealizedPnL", 0) for p in positions)
            return {
                "totalUnrealizedPnL": total_pnl,
                "positions": positions,
            }
        except Exception as exc:
            return {"error": {"message": f"Failed to get unrealized PnL: {exc}"}}

    @server.tool(
        description=(
            "Retrieves the current margin call status and threshold levels."
        ),
        annotations={
            "title": "Get Margin Call Status",
            "readOnlyHint": True,
            "openWorldHint": True,
        },
    )
    async def get_margin_call_status() -> dict:
        """Get margin call status."""
        try:
            return {
                "marginCallStatus": "unknown",
                "note": "Requires ProtoOAMarginCallListReq",
            }
        except Exception as exc:
            return {"error": {"message": f"Failed: {exc}"}}

    @server.tool(
        description=(
            "Calculates the expected margin for a hypothetical order."
        ),
        annotations={
            "title": "Get Expected Margin",
            "readOnlyHint": True,
            "openWorldHint": True,
        },
    )
    async def get_expected_margin(
        symbol_id: int, volume: int, trade_side: str = "BUY",
    ) -> dict:
        """Get expected margin for a hypothetical order."""
        try:
            return {
                "expectedMargin": 0,
                "note": "Requires ProtoOAExpectedMarginReq",
            }
        except Exception as exc:
            return {"error": {"message": f"Failed: {exc}"}}

    @server.tool(
        description=(
            "Retrieves the dynamic leverage tiers configured for the account."
        ),
        annotations={
            "title": "Get Dynamic Leverage",
            "readOnlyHint": True,
            "openWorldHint": True,
        },
    )
    async def get_dynamic_leverage() -> dict:
        """Get dynamic leverage tiers."""
        try:
            return {
                "dynamicLeverage": [],
                "note": "Requires ProtoOADynamicLeverageListReq",
            }
        except Exception as exc:
            return {"error": {"message": f"Failed: {exc}"}}

    @server.tool(
        description=(
            "Retrieves the cash flow history for the selected account."
        ),
        annotations={
            "title": "Get Cash Flow History",
            "readOnlyHint": True,
            "openWorldHint": True,
        },
    )
    async def get_cash_flow_history(
        from_timestamp: int = 0, to_timestamp: int = 0,
    ) -> dict:
        """Get cash flow history."""
        try:
            return {
                "cashFlow": [],
                "note": "Requires ProtoOACashFlowHistoryReq",
            }
        except Exception as exc:
            return {"error": {"message": f"Failed: {exc}"}}
