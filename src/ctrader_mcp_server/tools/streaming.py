"""
Streaming tools for the cTrader MCP Server.

Provides live spot-price, trendbar, and market-depth subscriptions
using a bounded event cache with non-blocking polling tools.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from fastmcp import FastMCP
    from ..session import CTraderSession


def register_streaming_tools(server: FastMCP, session: CTraderSession) -> None:
    """Register streaming tools on the given server."""

    @server.tool(
        description=(
            "Subscribes to live spot price updates for one or more symbols. "
            "Use poll_spots to retrieve buffered spot events."
        ),
        annotations={
            "title": "Subscribe Spots",
            "readOnlyHint": False,
            "destructiveHint": False,
            "openWorldHint": True,
        },
    )
    async def subscribe_spots(symbol_ids: str) -> dict:
        """Subscribe to live spot price updates."""
        try:
            ids = [int(s.strip()) for s in symbol_ids.split(",") if s.strip()]
            return await session.subscribe_spots(ids)
        except Exception as exc:
            return {"error": {"message": f"Failed to subscribe spots: {exc}"}}

    @server.tool(
        description="Unsubscribes from live spot price updates for one or more symbols.",
        annotations={
            "title": "Unsubscribe Spots",
            "readOnlyHint": False,
            "destructiveHint": False,
            "openWorldHint": True,
        },
    )
    async def unsubscribe_spots(symbol_ids: str) -> dict:
        """Unsubscribe from live spot price updates."""
        try:
            ids = [int(s.strip()) for s in symbol_ids.split(",") if s.strip()]
            return await session.unsubscribe_spots(ids)
        except Exception as exc:
            return {"error": {"message": f"Failed to unsubscribe spots: {exc}"}}

    @server.tool(
        description=(
            "Retrieves buffered live spot price events since the last poll. "
            "Non-blocking: returns immediately with available events."
        ),
        annotations={
            "title": "Poll Spots",
            "readOnlyHint": True,
            "openWorldHint": True,
        },
    )
    async def poll_spots(symbol_id: int = 0) -> dict:
        """Poll buffered spot price events."""
        try:
            if symbol_id > 0:
                events = session.streaming_cache.poll_spots(str(symbol_id))
                return {"symbolId": symbol_id, "spotEvents": events}
            all_events: dict = {}
            for key in list(session.streaming_cache._spots.keys()):
                all_events[key] = session.streaming_cache.poll_spots(key)
            return {"spotEvents": all_events}
        except Exception as exc:
            return {"error": {"message": f"Failed to poll spots: {exc}"}}
    @server.tool(
        description=(
            "Subscribes to live trendbar updates for a symbol and timeframe. "
            "Use poll_trendbars to retrieve buffered trendbar events."
        ),
        annotations={
            "title": "Subscribe Trendbars",
            "readOnlyHint": False,
            "destructiveHint": False,
            "openWorldHint": True,
        },
    )
    async def subscribe_trendbars(symbol_id: int, period: str = "M1") -> dict:
        """Subscribe to live trendbar updates."""
        try:
            return {"status": "not_implemented", "note": "Requires ProtoOASubscribeForTrendbarsReq"}
        except Exception as exc:
            return {"error": {"message": f"Failed to subscribe trendbars: {exc}"}}

    @server.tool(
        description="Unsubscribes from live trendbar updates for a symbol.",
        annotations={
            "title": "Unsubscribe Trendbars",
            "readOnlyHint": False,
            "destructiveHint": False,
            "openWorldHint": True,
        },
    )
    async def unsubscribe_trendbars(symbol_id: int) -> dict:
        """Unsubscribe from live trendbar updates."""
        try:
            return {"status": "not_implemented", "note": "Requires ProtoOAUnsubscribeForTrendbarsReq"}
        except Exception as exc:
            return {"error": {"message": f"Failed: {exc}"}}

    @server.tool(
        description="Retrieves buffered live trendbar events since the last poll.",
        annotations={
            "title": "Poll Trendbars",
            "readOnlyHint": True,
            "openWorldHint": True,
        },
    )
    async def poll_trendbars(symbol_id: int = 0) -> dict:
        """Poll buffered trendbar events."""
        try:
            if symbol_id > 0:
                events = session.streaming_cache.poll_trendbars(str(symbol_id))
                return {"symbolId": symbol_id, "trendbarEvents": events}
            all_events: dict = {}
            for key in list(session.streaming_cache._trendbars.keys()):
                all_events[key] = session.streaming_cache.poll_trendbars(key)
            return {"trendbarEvents": all_events}
        except Exception as exc:
            return {"error": {"message": f"Failed to poll trendbars: {exc}"}}

    @server.tool(
        description=(
            "Subscribes to live market depth (order book) updates for symbols. "
            "Use poll_depth to retrieve buffered depth events."
        ),
        annotations={
            "title": "Subscribe Depth",
            "readOnlyHint": False,
            "destructiveHint": False,
            "openWorldHint": True,
        },
    )
    async def subscribe_depth(symbol_ids: str) -> dict:
        """Subscribe to live market depth updates."""
        try:
            return {"status": "not_implemented", "note": "Requires ProtoOASubscribeDepthQuotesReq"}
        except Exception as exc:
            return {"error": {"message": f"Failed to subscribe depth: {exc}"}}

    @server.tool(
        description="Unsubscribes from live market depth updates for symbols.",
        annotations={
            "title": "Unsubscribe Depth",
            "readOnlyHint": False,
            "destructiveHint": False,
            "openWorldHint": True,
        },
    )
    async def unsubscribe_depth(symbol_ids: str) -> dict:
        """Unsubscribe from live market depth updates."""
        try:
            return {"status": "not_implemented", "note": "Requires ProtoOAUnsubscribeDepthQuotesReq"}
        except Exception as exc:
            return {"error": {"message": f"Failed: {exc}"}}

    @server.tool(
        description="Retrieves buffered market depth events since the last poll.",
        annotations={
            "title": "Poll Depth",
            "readOnlyHint": True,
            "openWorldHint": True,
        },
    )
    async def poll_depth(symbol_id: int = 0) -> dict:
        """Poll buffered market depth events."""
        try:
            if symbol_id > 0:
                events = session.streaming_cache.poll_depth(str(symbol_id))
                return {"symbolId": symbol_id, "depthEvents": events}
            all_events: dict = {}
            for key in list(session.streaming_cache._depth.keys()):
                all_events[key] = session.streaming_cache.poll_depth(key)
            return {"depthEvents": all_events}
        except Exception as exc:
            return {"error": {"message": f"Failed to poll depth: {exc}"}}

            return {"error": {"message": f"Failed to poll spots: {exc}"}}
