"""
Trading tools for the cTrader MCP Server.

Provides order placement, amendment, cancellation, position management,
and deal queries.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from fastmcp import FastMCP
    from ..session import CTraderSession


def register_trading_tools(server: FastMCP, session: CTraderSession) -> None:
    """Register trading tools on the given server."""

    @server.tool(
        description=(
            "Places a market order on the selected account. Executes "
            "immediately at the current market price."
        ),
        annotations={
            "title": "Place Market Order",
            "readOnlyHint": False,
            "destructiveHint": True,
            "idempotentHint": False,
            "openWorldHint": True,
        },
    )
    async def place_market_order(
        symbol_id: int,
        trade_side: str,
        volume: int,
        client_order_id: str = "",
        stop_loss: float = 0,
        take_profit: float = 0,
    ) -> dict:
        """Place a market order."""
        try:
            return await session.place_order(
                symbol_id=symbol_id,
                trade_side=trade_side,
                volume=volume,
                order_type="MARKET",
                client_order_id=client_order_id,
                stop_loss=stop_loss,
                take_profit=take_profit,
            )
        except Exception as exc:
            return {"error": {"message": f"Failed to place market order: {exc}"}}

    @server.tool(
        description=(
            "Places a limit order on the selected account."
        ),
        annotations={
            "title": "Place Limit Order",
            "readOnlyHint": False,
            "destructiveHint": True,
            "idempotentHint": False,
            "openWorldHint": True,
        },
    )
    async def place_limit_order(
        symbol_id: int,
        trade_side: str,
        volume: int,
        limit_price: float,
        client_order_id: str = "",
        stop_loss: float = 0,
        take_profit: float = 0,
    ) -> dict:
        """Place a limit order."""
        try:
            return await session.place_order(
                symbol_id=symbol_id,
                trade_side=trade_side,
                volume=volume,
                order_type="LIMIT",
                limit_price=limit_price,
                client_order_id=client_order_id,
                stop_loss=stop_loss,
                take_profit=take_profit,
            )
        except Exception as exc:
            return {"error": {"message": f"Failed to place limit order: {exc}"}}

    @server.tool(
        description=(
            "Places a stop order on the selected account."
        ),
        annotations={
            "title": "Place Stop Order",
            "readOnlyHint": False,
            "destructiveHint": True,
            "idempotentHint": False,
            "openWorldHint": True,
        },
    )
    async def place_stop_order(
        symbol_id: int,
        trade_side: str,
        volume: int,
        stop_price: float,
        client_order_id: str = "",
        stop_loss: float = 0,
        take_profit: float = 0,
    ) -> dict:
        """Place a stop order."""
        try:
            return await session.place_order(
                symbol_id=symbol_id,
                trade_side=trade_side,
                volume=volume,
                order_type="STOP",
                stop_price=stop_price,
                client_order_id=client_order_id,
                stop_loss=stop_loss,
                take_profit=take_profit,
            )
        except Exception as exc:
            return {"error": {"message": f"Failed to place stop order: {exc}"}}

    @server.tool(
        description="Amends an existing pending order.",
        annotations={
            "title": "Amend Order",
            "readOnlyHint": False,
            "destructiveHint": False,
            "openWorldHint": True,
        },
    )
    async def amend_order(
        order_id: int,
        limit_price: Optional[float] = None,
        stop_price: Optional[float] = None,
        volume: Optional[int] = None,
    ) -> dict:
        """Amend an existing pending order."""
        try:
            return {"status": "not_implemented", "note": "Requires ProtoOAAmendOrderReq"}
        except Exception as exc:
            return {"error": {"message": f"Failed to amend order: {exc}"}}

    @server.tool(
        description="Cancels an existing pending order on the selected account.",
        annotations={
            "title": "Cancel Order",
            "readOnlyHint": False,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": True,
        },
    )
    async def cancel_order(order_id: int) -> dict:
        """Cancel a pending order."""
        try:
            return await session.cancel_order(order_id)
        except Exception as exc:
            return {"error": {"message": f"Failed to cancel order: {exc}"}}

    @server.tool(
        description="Retrieves the list of pending orders on the selected account.",
        annotations={
            "title": "Get Orders",
            "readOnlyHint": True,
            "openWorldHint": True,
        },
    )
    async def get_orders() -> dict:
        """Get pending orders."""
        try:
            orders = await session.get_orders()
            return {"orders": orders}
        except Exception as exc:
            return {"error": {"message": f"Failed to get orders: {exc}"}}

    @server.tool(
        description="Retrieves a single order by its ID on the selected account.",
        annotations={
            "title": "Get Order By ID",
            "readOnlyHint": True,
            "openWorldHint": True,
        },
        )
    async def get_order_by_id(order_id: int) -> dict:
        """Get a single order by ID."""
        try:
            orders = await session.get_orders()
            order = next(
                (o for o in orders if o.get("orderId") == order_id), None
            )
            if order is None:
                return {"error": {"message": f"Order {order_id} not found"}}
            return order
        except Exception as exc:
                                    return {"error": {"message": f"Failed to get order: {exc}"}}

    @server.tool(
        description="Retrieves all open positions on the selected account.",
        annotations={
            "title": "Get Positions",
            "readOnlyHint": True,
            "openWorldHint": True,
        },
    )
    async def get_positions() -> dict:
        """Get all open positions."""
        try:
            positions = await session.get_positions()
            return {"positions": positions}
        except Exception as exc:
            return {"error": {"message": f"Failed to get positions: {exc}"}}

    @server.tool(
        description="Retrieves a single open position by its ID.",
        annotations={
            "title": "Get Position By ID",
            "readOnlyHint": True,
            "openWorldHint": True,
        },
    )
    async def get_position_by_id(position_id: int) -> dict:
        """Get a single position by ID."""
        try:
            positions = await session.get_positions()
            pos = next(
                (p for p in positions if p.get("positionId") == position_id), None
            )
            if pos is None:
                return {"error": {"message": f"Position {position_id} not found"}}
            return pos
        except Exception as exc:
            return {"error": {"message": f"Failed to get position: {exc}"}}

    @server.tool(
        description="Closes an open position on the selected account.",
        annotations={
            "title": "Close Position",
            "readOnlyHint": False,
            "destructiveHint": True,
            "idempotentHint": False,
            "openWorldHint": True,
        },
    )
    async def close_position(position_id: int, volume: int = 0) -> dict:
        """Close an open position."""
        try:
            return await session.close_position(position_id, volume)
        except Exception as exc:
            return {"error": {"message": f"Failed to close position: {exc}"}}

    @server.tool(
        description="Closes all open positions on the selected account.",
        annotations={
            "title": "Close All Positions",
            "readOnlyHint": False,
            "destructiveHint": True,
            "idempotentHint": False,
            "openWorldHint": True,
        },
    )
    async def close_all_positions() -> dict:
        """Close all open positions."""
        try:
            positions = await session.get_positions()
            results = []
            for pos in positions:
                result = await session.close_position(pos["positionId"])
                results.append(result)
            return {"closed": results}
        except Exception as exc:
            return {"error": {"message": f"Failed to close all positions: {exc}"}}

    @server.tool(
        description="Retrieves the list of executed deals (fills) on the account.",
        annotations={
            "title": "Get Deals",
            "readOnlyHint": True,
            "openWorldHint": True,
        },
    )
    async def get_deals(
        from_timestamp: int = 0, to_timestamp: int = 0,
    ) -> dict:
        """Get executed deals."""
        try:
            return {"deals": [], "note": "Requires ProtoOADealListReq"}
        except Exception as exc:
            return {"error": {"message": f"Failed to get deals: {exc}"}}

    @server.tool(
        description="Retrieves the deals (fills) associated with a specific position.",
        annotations={
            "title": "Get Deals By Position",
            "readOnlyHint": True,
            "openWorldHint": True,
        },
    )
    async def get_deals_by_position(position_id: int) -> dict:
        """Get deals for a specific position."""
        try:
            return {"deals": [], "note": "Requires ProtoOADealListByPositionIdReq"}
        except Exception as exc:
            return {"error": {"message": f"Failed to get deals: {exc}"}}

