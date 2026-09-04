"""
cTrader MCP Server — FastMCP + curated tools.

Builds MCP tools for the cTrader Open API at process init time.
All tools are hand-crafted wrappers around the session manager.
"""

from __future__ import annotations

import os
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

from fastmcp import FastMCP

from .config import load_config
from .oauth import OAuthManager
from .security import TrustBoundaryMiddleware
from .session import CTraderSession
from .toolsets import get_active_tools

from .tools.auth import register_auth_tools
from .tools.account import register_account_tools
from .tools.trading import register_trading_tools
from .tools.market_data import register_market_data_tools
from .tools.streaming import register_streaming_tools
from .tools.diagnostics import register_diagnostics_tools


def _parse_toolsets() -> set[str] | None:
    """Parse CTRADER_TOOLSETS env var into a set of toolset names."""
    raw = os.environ.get("CTRADER_TOOLSETS", "").strip()
    if not raw:
        return None
    return {t.strip() for t in raw.split(",") if t.strip()}


def build_server() -> FastMCP:
    """Construct the cTrader MCP server with all curated tools."""
    config = load_config()

    # Build OAuthManager. If client_id/secret are provided, use the full OAuth
    # flow (token discovery, refresh). Otherwise, seed the manager with the
    # access token from config — no OAuth exchange needed.
    if config.client_id and config.client_secret:
        oauth = OAuthManager(
            client_id=config.client_id,
            client_secret=config.client_secret,
            redirect_uri=config.redirect_uri,
            token_path=config.token_path,
        )
    else:
        oauth = OAuthManager.from_access_token(
            access_token=config.access_token,
            token_path=config.token_path,
        )

    session = CTraderSession(config=config, oauth=oauth)

    active_toolsets = _parse_toolsets()
    active_tools = get_active_tools(active_toolsets)

    @asynccontextmanager
    async def lifespan(_server: FastMCP) -> AsyncIterator[dict]:
        try:
            yield {}
        finally:
            await session.disconnect()

    main = FastMCP("cTrader MCP Server", lifespan=lifespan)
    main.add_middleware(TrustBoundaryMiddleware())

    # Register tool groups
    if active_tools & set(get_active_tools({"auth"})):
        register_auth_tools(main, oauth, session)
    if active_tools & set(get_active_tools({"account"})):
        register_account_tools(main, session)
    if active_tools & set(get_active_tools({"trading"})):
        register_trading_tools(main, session)
    if active_tools & set(get_active_tools({"market_data"})):
        register_market_data_tools(main, session)
    if active_tools & set(get_active_tools({"streaming"})):
        register_streaming_tools(main, session)
    if active_tools & set(get_active_tools({"diagnostics"})):
        register_diagnostics_tools(main, session)

    return main
