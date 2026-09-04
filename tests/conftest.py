"""Shared fixtures for the cTrader MCP Server test suite."""

from __future__ import annotations

import os
from pathlib import Path
from typing import AsyncIterator

import pytest
from fastmcp.client import Client

from ctrader_mcp_server.config import ServerConfig, Environment
from ctrader_mcp_server.oauth import OAuthManager
from ctrader_mcp_server.session import CTraderSession


DUMMY_ENV = {
    "CTRADER_CLIENT_ID": "test-client-id",
    "CTRADER_CLIENT_SECRET": "test-client-secret",
    "CTRADER_ENVIRONMENT": "demo",
    "CTRADER_ACCOUNT_ID": "12345",
}


@pytest.fixture
def dummy_config(tmp_path: Path) -> ServerConfig:
    """Create a dummy server config for testing."""
    return ServerConfig(
        client_id="test-client-id",
        client_secret="test-client-secret",
        redirect_uri="http://localhost:8080/callback",
        environment=Environment.DEMO,
        account_id="12345",
        token_path=tmp_path / "tokens.json",
        request_timeout=5,
    )


@pytest.fixture
def dummy_oauth(tmp_path: Path) -> OAuthManager:
    """Create a dummy OAuth manager for testing."""
    return OAuthManager(
        client_id="test-client-id",
        client_secret="test-client-secret",
        redirect_uri="http://localhost:8080/callback",
        token_path=tmp_path / "tokens.json",
    )


@pytest.fixture
def dummy_session(dummy_config: ServerConfig, dummy_oauth: OAuthManager) -> CTraderSession:
    """Create a dummy session for testing."""
    return CTraderSession(config=dummy_config, oauth=dummy_oauth)
