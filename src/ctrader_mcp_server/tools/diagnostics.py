"""
Diagnostics tools for the cTrader MCP Server.

Provides protocol version and connection status queries.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from fastmcp import FastMCP
    from ..session import CTraderSession


def register_diagnostics_tools(server: FastMCP, session: CTraderSession) -> None:
    """Register diagnostics tools on the given server."""

    @server.tool(
        description=(
            "Retrieves the cTrader Open API protocol version. "
            "Useful for debugging compatibility issues."
        ),
        annotations={
            "title": "Get Protocol Version",
            "readOnlyHint": True,
            "openWorldHint": True,
        },
    )
    async def get_protocol_version() -> dict:
        """Get the protocol version.

        Returns:
            A dict with the protocol version string.
        """
        try:
            version = await session.get_protocol_version()
            return {"protocolVersion": version}
        except Exception as exc:
            return {"error": {"message": f"Failed to get protocol version: {exc}"}}

    @server.tool(
        description=(
            "Returns the current connection status including whether "
            "the client is connected, authenticated, and which account "
            "is selected."
        ),
        annotations={
            "title": "Get Connection Status",
            "readOnlyHint": True,
            "openWorldHint": True,
        },
    )
    async def get_connection_status() -> dict:
        """Get the current connection status.

        Returns:
            A dict with connection and authentication status.
        """
        state = session.state
        return {
            "connected": state.connected,
            "applicationAuthenticated": state.application_authenticated,
            "accountAuthenticated": state.account_authenticated,
            "accountId": state.account_id,
            "protocolVersion": state.protocol_version,
            "reconnectAttempts": state.reconnect_attempts,
            "lastError": state.last_error,
        }
