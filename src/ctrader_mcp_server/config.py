"""
Server-side configuration for the cTrader MCP Server.

All sensitive values (client_id, client_secret, tokens) are read from
environment variables or an env file. Secrets are never accepted as
MCP tool arguments, logged, or included in responses.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Optional


class Environment(str, Enum):
    """cTrader trading environment."""

    DEMO = "demo"
    LIVE = "live"


# cTrader OAuth endpoints (from the cTrader OpenApiPy SDK)
AUTH_URI = "https://openapi.ctrader.com/apps/auth"
TOKEN_URI = "https://openapi.ctrader.com/apps/token"

# cTrader protobuf endpoints (from the cTrader OpenApiPy SDK EndPoints class)
PROTOBUF_DEMO_HOST = "demo.ctraderapi.com"
PROTOBUF_LIVE_HOST = "live.ctraderapi.com"
PROTOBUF_PORT = 5035

# Default local OAuth redirect URI
DEFAULT_REDIRECT_URI = "http://localhost:8080/callback"

# Token storage path (local file for refresh/access tokens)
DEFAULT_TOKEN_PATH = Path.home() / ".ctrader_mcp_server" / "tokens.json"

# Request timeout in seconds
DEFAULT_REQUEST_TIMEOUT = 30

# Heartbeat interval in seconds (cTrader sends heartbeat every 20s)
HEARTBEAT_INTERVAL = 20

# Max reconnect attempts
MAX_RECONNECT_ATTEMPTS = 3

# Streaming event cache size
STREAMING_CACHE_SIZE = 1000


@dataclass(frozen=True)
class ServerConfig:
    """Immutable server configuration derived from environment.

    Attributes:
        client_id: Permanent cTrader application client ID.
        client_secret: Permanent cTrader application client secret.
        redirect_uri: Local OAuth redirect URI for the authorization-code flow.
        environment: Demo or live trading environment.
        account_id: The selected cTrader account ID to operate on.
        token_path: Path for persistent token storage.
        request_timeout: Timeout in seconds for API requests.
    """

    client_id: str
    client_secret: str
    redirect_uri: str = DEFAULT_REDIRECT_URI
    environment: Environment = Environment.DEMO
    account_id: str = ""
    token_path: Path = field(default_factory=lambda: DEFAULT_TOKEN_PATH)
    request_timeout: int = DEFAULT_REQUEST_TIMEOUT

    def get_host(self) -> str:
        """Return the protobuf host for the configured environment."""
        if self.environment == Environment.LIVE:
            return PROTOBUF_LIVE_HOST
        return PROTOBUF_DEMO_HOST

    def get_port(self) -> int:
        """Return the protobuf port."""
        return PROTOBUF_PORT


def _parse_environment(raw: str) -> Environment:
    """Parse an environment string, defaulting to demo."""
    normalized = raw.strip().lower()
    if normalized in ("live", "real", "production"):
        return Environment.LIVE
    return Environment.DEMO


def load_config(
    env_file: Optional[Path] = None,
) -> ServerConfig:
    """Load configuration from environment variables.

    Args:
        env_file: Optional path to a .env file to load before reading.

    Returns:
        ServerConfig with all required fields populated.

    Raises:
        ValueError: If required credentials are missing.
    """
    if env_file is not None:
        from dotenv import load_dotenv

        load_dotenv(env_file, override=False)

    client_id = os.environ.get("CTRADER_CLIENT_ID", "").strip()
    client_secret = os.environ.get("CTRADER_CLIENT_SECRET", "").strip()

    if not client_id:
        raise ValueError(
            "CTRADER_CLIENT_ID must be set. "
            "Set it in your MCP client config's env block or pass --env-file."
        )
    if not client_secret:
        raise ValueError(
            "CTRADER_CLIENT_SECRET must be set. "
            "Set it in your MCP client config's env block or pass --env-file."
        )

    redirect_uri = os.environ.get(
        "CTRADER_REDIRECT_URI", DEFAULT_REDIRECT_URI
    ).strip()

    environment = _parse_environment(os.environ.get("CTRADER_ENVIRONMENT", "demo"))

    account_id = os.environ.get("CTRADER_ACCOUNT_ID", "").strip()

    token_path_raw = os.environ.get("CTRADER_TOKEN_PATH", "")
    token_path = Path(token_path_raw) if token_path_raw else DEFAULT_TOKEN_PATH

    timeout_raw = os.environ.get("CTRADER_REQUEST_TIMEOUT", "")
    request_timeout = int(timeout_raw) if timeout_raw.isdigit() else DEFAULT_REQUEST_TIMEOUT

    return ServerConfig(
        client_id=client_id,
        client_secret=client_secret,
        redirect_uri=redirect_uri,
        environment=environment,
        account_id=account_id,
        token_path=token_path,
        request_timeout=request_timeout,
    )
