"""
Tests for the OAuth authorization-code flow.

Covers:
- Authorization URL generation
- Token exchange (mocked HTTP)
- Token refresh (mocked HTTP)
- Token persistence and loading
- Token expiry detection
- Status reporting (no secret exposure)
"""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from ctrader_mcp_server.oauth import OAuthManager, OAuthError, TokenData


@pytest.fixture
def oauth(tmp_path: Path) -> OAuthManager:
    """Create an OAuth manager for testing."""
    return OAuthManager(
        client_id="test-client-id",
        client_secret="test-client-secret",
        redirect_uri="http://localhost:8080/callback",
        token_path=tmp_path / "tokens.json",
    )


def test_get_authorization_url(oauth: OAuthManager):
    """Authorization URL should contain the client_id and redirect_uri."""
    url = oauth.get_authorization_url()
    assert "client_id=test-client-id" in url
    assert "redirect_uri=http%3A%2F%2Flocalhost%3A8080%2Fcallback" in url
    assert url.startswith("https://openapi.ctrader.com/apps/auth")


def test_get_authorization_url_with_scope(oauth: OAuthManager):
    """Authorization URL should include the scope parameter."""
    url = oauth.get_authorization_url(scope="trading")
    assert "scope=trading" in url


def test_initial_status_not_authorized(oauth: OAuthManager):
    """Initial status should indicate not authorized."""
    status = oauth.get_status()
    assert status["authorized"] is False


def test_token_data_expiry():
    """TokenData should correctly detect expiry."""
    import time

    expired = TokenData(
        access_token="at", refresh_token="rt", expires_at=time.time() - 100,
    )
    assert expired.is_expired is True

    valid = TokenData(
        access_token="at", refresh_token="rt", expires_at=time.time() + 3600,
    )
    assert valid.is_expired is False


def test_token_data_serialization():
    """TokenData should serialize and deserialize correctly."""
    import time

    original = TokenData(
        access_token="my-access-token",
        refresh_token="my-refresh-token",
        expires_at=time.time() + 3600,
        token_type="Bearer",
        scope="trading",
    )
    data = original.to_dict()
    restored = TokenData.from_dict(data)
    assert restored.access_token == original.access_token
    assert restored.refresh_token == original.refresh_token
    assert restored.token_type == original.token_type
    assert restored.scope == original.scope
    assert restored.expires_at == original.expires_at


@pytest.mark.asyncio
async def test_exchange_code_success(oauth: OAuthManager, tmp_path: Path):
    """Successful token exchange should store tokens and update status."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "access_token": "new-access-token",
        "refresh_token": "new-refresh-token",
        "expires_in": 3600,
        "token_type": "Bearer",
        "scope": "trading",
    }

    with patch("httpx.AsyncClient") as mock_client_class:
        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_client_class.return_value.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client_class.return_value.__aexit__ = AsyncMock(return_value=False)

        result = await oauth.exchange_code("test-auth-code")

    assert result["authorized"] is True
    assert oauth.is_authorized is True
    assert oauth.access_token == "new-access-token"

    token_file = tmp_path / "tokens.json"
    assert token_file.exists()
    saved_data = json.loads(token_file.read_text())
    assert saved_data["access_token"] == "new-access-token"


@pytest.mark.asyncio
async def test_exchange_code_failure(oauth: OAuthManager):
    """Failed token exchange should raise OAuthError."""
    mock_response = MagicMock()
    mock_response.status_code = 400
    mock_response.text = "Invalid authorization code"

    with patch("httpx.AsyncClient") as mock_client_class:
        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_client_class.return_value.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client_class.return_value.__aexit__ = AsyncMock(return_value=False)

        with pytest.raises(OAuthError) as exc_info:
            await oauth.exchange_code("bad-code")

    assert exc_info.value.http_status == 400


@pytest.mark.asyncio
async def test_refresh_access_token_success(oauth: OAuthManager):
    """Successful token refresh should update the access token."""
    import time
    oauth._token = TokenData(
        access_token="old-access-token",
        refresh_token="my-refresh-token",
        expires_at=time.time() - 100,
    )

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "access_token": "refreshed-access-token",
        "refresh_token": "new-refresh-token",
        "expires_in": 3600,
        "token_type": "Bearer",
        "scope": "trading",
    }

    with patch("httpx.AsyncClient") as mock_client_class:
        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_client_class.return_value.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client_class.return_value.__aexit__ = AsyncMock(return_value=False)

        result = await oauth.refresh_access_token()

    assert result["authorized"] is True
    assert oauth.access_token == "refreshed-access-token"


@pytest.mark.asyncio
async def test_refresh_without_token_fails(oauth: OAuthManager):
    """Refreshing without a stored token should raise OAuthError."""
    with pytest.raises(OAuthError, match="No refresh token available"):
        await oauth.refresh_access_token()


def test_status_does_not_expose_secrets(oauth: OAuthManager):
    """Status output must never contain token values."""
    oauth._token = TokenData(
        access_token="secret-access-token",
        refresh_token="secret-refresh-token",
        expires_at=9999999999,
    )
    status = oauth.get_status()
    status_str = json.dumps(status)
    assert "secret-access-token" not in status_str
    assert "secret-refresh-token" not in status_str


def test_tokens_persisted_and_loaded(tmp_path: Path):
    """Tokens should be saved and loaded from disk."""
    token_file = tmp_path / "tokens.json"
    token_data = {
        "access_token": "loaded-at",
        "refresh_token": "loaded-rt",
        "expires_at": 9999999999,
        "token_type": "Bearer",
        "scope": "trading",
    }
    token_file.write_text(json.dumps(token_data))

    oauth = OAuthManager(
        client_id="test-id",
        client_secret="test-secret",
        redirect_uri="http://localhost/callback",
        token_path=token_file,
    )

    assert oauth.access_token == "loaded-at"
    assert oauth.is_authorized is True
