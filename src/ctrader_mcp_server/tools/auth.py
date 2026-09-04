"""
Auth tools for the cTrader MCP Server.

Implements the OAuth authorization-code flow:
- get_authorization_url: Returns the URL for the user to authorize
- exchange_authorization_code: Exchanges the code for tokens
- refresh_access_token: Refreshes the access token
- get_authorization_status: Returns current auth status
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from fastmcp import FastMCP
    from ..oauth import OAuthManager
    from ..session import CTraderSession


def register_auth_tools(server: FastMCP, oauth: OAuthManager, session: CTraderSession) -> None:
    """Register auth tools on the given server."""

    @server.tool(
        description=(
            "Returns the cTrader OAuth authorization URL. The user must open "
            "this URL in a browser to authorize the application."
        ),
        annotations={
            "title": "Get Authorization URL",
            "readOnlyHint": True,
            "openWorldHint": True,
        },
    )
    async def get_authorization_url(scope: str = "trading") -> dict:
        """Get the OAuth authorization URL.

        Args:
            scope: OAuth scope (default: "trading").

        Returns:
            A dict with the authorization URL and instructions.
        """
        url = oauth.get_authorization_url(scope=scope)
        return {
            "authorization_url": url,
            "instructions": (
                "Open this URL in a browser to authorize the application. "
                "After authorization, cTrader will redirect to the local "
                "callback URI with an authorization code. Use "
                "exchange_authorization_code with that code."
            ),
        }

    @server.tool(
        description=(
            "Exchanges an OAuth authorization code for access and refresh tokens."
        ),
        annotations={
            "title": "Exchange Authorization Code",
            "readOnlyHint": False,
            "destructiveHint": False,
            "openWorldHint": True,
        },
    )
    async def exchange_authorization_code(authorization_code: str) -> dict:
        """Exchange an authorization code for tokens.

        Args:
            authorization_code: The code received from the OAuth callback.

        Returns:
            A dict with the authorization status.
        """
        try:
            return await oauth.exchange_code(authorization_code)
        except Exception as exc:
            return {"error": {"message": f"Token exchange failed: {exc}"}}

    @server.tool(
        description=(
            "Refreshes the access token using the stored refresh token."
        ),
        annotations={
            "title": "Refresh Access Token",
            "readOnlyHint": False,
            "destructiveHint": False,
            "openWorldHint": True,
        },
    )
    async def refresh_access_token() -> dict:
        """Refresh the access token.

        Returns:
            A dict with the updated authorization status.
        """
        try:
            return await oauth.refresh_access_token()
        except Exception as exc:
            return {"error": {"message": f"Token refresh failed: {exc}"}}

    @server.tool(
        description=(
            "Returns the current authorization status including whether "
            "tokens are valid and when they expire."
        ),
        annotations={
            "title": "Get Authorization Status",
            "readOnlyHint": True,
            "openWorldHint": True,
        },
    )
    async def get_authorization_status() -> dict:
        """Get the current authorization status.

        Returns:
            A dict with authorization status information.
        """
        return oauth.get_status()
