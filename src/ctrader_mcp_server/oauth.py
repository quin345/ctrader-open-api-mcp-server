"""Local OAuth authorization-code flow for cTrader."""

from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional
from urllib.parse import urlencode

import httpx

from .config import AUTH_URI, TOKEN_URI


@dataclass
class TokenData:
    """OAuth token state."""

    access_token: str
    refresh_token: str
    expires_at: float
    token_type: str = "Bearer"
    scope: str = "trading"

    @property
    def is_expired(self) -> bool:
        return time.time() >= (self.expires_at - 60)

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "TokenData":
        return cls(
            access_token=data.get("access_token", ""),
            refresh_token=data.get("refresh_token", ""),
            expires_at=data.get("expires_at", 0.0),
            token_type=data.get("token_type", "Bearer"),
            scope=data.get("scope", "trading"),
        )


class OAuthError(Exception):
    """Raised when an OAuth operation fails."""

    def __init__(
        self,
        message: str,
        http_status: Optional[int] = None,
        detail: Optional[str] = None,
    ):
        super().__init__(message)
        self.http_status = http_status
        self.detail = detail



class OAuthManager:
    """Manages the cTrader OAuth authorization-code flow."""

    def __init__(
        self,
        client_id: str,
        client_secret: str,
        redirect_uri: str,
        token_path: Path,
    ):
        self._client_id = client_id
        self._client_secret = client_secret
        self._redirect_uri = redirect_uri
        self._token_path = token_path
        self._token: Optional[TokenData] = None
        self._load_tokens()

    def get_authorization_url(self, scope: str = "trading") -> str:
        """Build the cTrader OAuth authorization URL."""
        params = {
            "client_id": self._client_id,
            "redirect_uri": self._redirect_uri,
            "scope": scope,
            "response_type": "code",
        }
        return f"{AUTH_URI}?{urlencode(params)}"

    async def exchange_code(self, authorization_code: str) -> dict:
        """Exchange an authorization code for access and refresh tokens."""
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                TOKEN_URI,
                data={
                    "grant_type": "authorization_code",
                    "code": authorization_code,
                    "redirect_uri": self._redirect_uri,
                    "client_id": self._client_id,
                    "client_secret": self._client_secret,
                                },
            )

        if response.status_code != 200:
            raise OAuthError(
                f"Token exchange failed: HTTP {response.status_code}",
                http_status=response.status_code,
                detail=response.text,
            )

        data = response.json()
        self._store_token_data(data)
        return self.get_status()

    async def refresh_access_token(self) -> dict:
        """Refresh the access token using the stored refresh token."""
        if self._token is None or not self._token.refresh_token:
            raise OAuthError("No refresh token available. Authorize first.")

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                TOKEN_URI,
                data={
                    "grant_type": "refresh_token",
                    "refresh_token": self._token.refresh_token,
                    "client_id": self._client_id,
                    "client_secret": self._client_secret,
                },
            )

        if response.status_code != 200:
            raise OAuthError(
                f"Token refresh failed: HTTP {response.status_code}",
                http_status=response.status_code,
                detail=response.text,
            )

        data = response.json()
        self._store_token_data(data)
        return self.get_status()

    def get_status(self) -> dict:
        """Return the current authorization status (no secret values)."""
        if self._token is None:
            return {
                "authorized": False,
                "message": "Not authorized. Use get_authorization_url to start.",
            }

        return {
            "authorized": True,
            "access_token_expired": self._token.is_expired,
            "expires_at": datetime.fromtimestamp(
                self._token.expires_at, tz=timezone.utc
            ).isoformat(),
            "scope": self._token.scope,
            "token_type": self._token.token_type,
        }

    @property
    def access_token(self) -> Optional[str]:
        """Return the current access token, or None if not authorized."""
        if self._token is None:
            return None
        return self._token.access_token

    @property
    def is_authorized(self) -> bool:
        """Check if we have a valid (non-expired) access token."""
        if self._token is None:
            return False
        return not self._token.is_expired

    def _store_token_data(self, data: dict) -> None:
        expires_in = data.get("expires_in", 3600)
        expires_at = time.time() + float(expires_in)

        refresh_token = data.get("refresh_token", "")
        if not refresh_token and self._token is not None:
            refresh_token = self._token.refresh_token

        self._token = TokenData(
            access_token=data.get("access_token", ""),
            refresh_token=refresh_token,
            expires_at=expires_at,
            token_type=data.get("token_type", "Bearer"),
            scope=data.get("scope", "trading"),
        )
        self._save_tokens()

    def _save_tokens(self) -> None:
        """Persist tokens to disk with restricted file permissions."""
        if self._token is None:
            return

        self._token_path.parent.mkdir(parents=True, exist_ok=True)
        data = self._token.to_dict()

        self._token_path.write_text(
            json.dumps(data, indent=2),
            encoding="utf-8",
        )
        try:
            os.chmod(self._token_path, 0o600)
        except (OSError, AttributeError):
            pass  # Windows or unsupported; ignore

    def _load_tokens(self) -> None:
        """Load tokens from disk if available."""
        if not self._token_path.exists():
            return

        try:
            data = json.loads(self._token_path.read_text(encoding="utf-8"))
            self._token = TokenData.from_dict(data)
        except (json.JSONDecodeError, KeyError, OSError):
            self._token = None

