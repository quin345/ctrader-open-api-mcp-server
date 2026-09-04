"""
Market data tools for the cTrader MCP Server.

Provides symbol metadata, historical trendbars, and tick data.
"""

from __future__ import annotations

import re
from datetime import datetime, timedelta, timezone
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from fastmcp import FastMCP
    from ..session import CTraderSession


_TIMEFRAME_ALIASES: dict[str, str] = {
    "m1": "M1", "m5": "M5", "m15": "M15", "m30": "M30",
    "h1": "H1", "h4": "H4",
    "d1": "D1", "w1": "W1", "mn1": "MN1",
}

_TIMEFRAME_PATTERN = re.compile(r"^(\d+)(m|h|d|w|mn)$")


def _normalize_timeframe(tf: str) -> str:
    """Map case variants to API-expected format."""
    lower = tf.lower().strip()
    alias = _TIMEFRAME_ALIASES.get(lower)
    if alias:
        return alias
    m = _TIMEFRAME_PATTERN.match(lower)
    if m:
        return m.group(1) + m.group(2).upper()
    return tf


def _relative_start(days: int = 0, hours: int = 0, minutes: int = 0) -> int:
    """Compute Unix timestamp (seconds) as now(UTC) minus the given offset."""
    if days == 0 and hours == 0 and minutes == 0:
        return 0
    start = datetime.now(timezone.utc) - timedelta(
        days=days, hours=hours, minutes=minutes
    )
    return int(start.timestamp())


def register_market_data_tools(server: FastMCP, session: CTraderSession) -> None:
    """Register market data tools on the given server."""

    @server.tool(
        description="Retrieves the list of tradable symbols available on the account.",
        annotations={
            "title": "Get Symbols",
            "readOnlyHint": True,
            "openWorldHint": True,
        },
    )
    async def get_symbols() -> dict:
        """Get tradable symbols."""
        try:
            symbols = await session.get_symbols()
            return {"symbols": symbols}
        except Exception as exc:
            return {"error": {"message": f"Failed to get symbols: {exc}"}}

    @server.tool(
        description="Retrieves detailed metadata for a specific symbol by its ID.",
        annotations={
            "title": "Get Symbol By ID",
            "readOnlyHint": True,
            "openWorldHint": True,
        },
    )
    async def get_symbol_by_id(symbol_id: int) -> dict:
        """Get symbol metadata by ID."""
        try:
            return {"symbolId": symbol_id, "note": "Requires ProtoOASymbolByIdReq"}
        except Exception as exc:
            return {"error": {"message": f"Failed to get symbol: {exc}"}}

    @server.tool(
        description="Retrieves the list of symbol pairs available for currency conversion.",
        annotations={
            "title": "Get Conversion Symbols",
            "readOnlyHint": True,
            "openWorldHint": True,
        },
    )
    async def get_conversion_symbols() -> dict:
        """Get conversion symbol pairs."""
        try:
            return {"conversionSymbols": [], "note": "Requires ProtoOASymbolListReq"}
        except Exception as exc:
            return {"error": {"message": f"Failed: {exc}"}}

    @server.tool(
        description=(
            "Retrieves historical trendbars (OHLC bars) for a symbol. "
            "Supports relative lookback and absolute time ranges."
        ),
        annotations={
            "title": "Get Trendbars",
            "readOnlyHint": True,
            "openWorldHint": True,
        },
    )
    async def get_trendbars(
        symbol_id: int,
        period: str = "M1",
        from_timestamp: int = 0,
        to_timestamp: int = 0,
        days: int = 0,
        hours: int = 0,
        minutes: int = 60,
    ) -> dict:
        """Get historical trendbars."""
        try:
            normalized_period = _normalize_timeframe(period)
            if from_timestamp == 0:
                from_timestamp = _relative_start(days=days, hours=hours, minutes=minutes)
            bars = await session.get_trendbars(
                symbol_id=symbol_id,
                period=normalized_period,
                from_ts=from_timestamp,
                to_ts=to_timestamp,
            )
            return {"symbolId": symbol_id, "period": normalized_period, "trendbars": bars}
        except Exception as exc:
            return {"error": {"message": f"Failed to get trendbars: {exc}"}}

    @server.tool(
        description="Retrieves historical tick-level price data for a symbol.",
        annotations={
            "title": "Get Tick Data",
            "readOnlyHint": True,
            "openWorldHint": True,
        },
    )
    async def get_tick_data(
        symbol_id: int,
        from_timestamp: int = 0,
        to_timestamp: int = 0,
        days: int = 0,
        hours: int = 0,
        minutes: int = 60,
    ) -> dict:
        """Get historical tick data."""
        try:
            if from_timestamp == 0:
                from_timestamp = _relative_start(days=days, hours=hours, minutes=minutes)
            return {"symbolId": symbol_id, "tickData": [], "note": "Requires ProtoOAGetTickDataReq"}
        except Exception as exc:
            return {"error": {"message": f"Failed to get tick data: {exc}"}}

