"""
Tests for the TrustBoundaryMiddleware trust-boundary envelope.

Covers:
- Middleware wraps structured tool results in the envelope
- Middleware uses risk-appropriate warning text
- Middleware does NOT double-wrap results
- Secret redaction works correctly
- Log sanitization works correctly
"""

from __future__ import annotations

import os
from unittest.mock import patch

import pytest

from fastmcp import FastMCP
from fastmcp.client import Client

from ctrader_mcp_server.security import (
    DATA_KEY,
    INSTRUCTIONS,
    SECURITY_KEY,
    WRAPPED_MARKER,
    TrustBoundaryMiddleware,
    redact_secrets,
    sanitize_for_log,
)

DUMMY_ENV = {
    "CTRADER_CLIENT_ID": "test-key",
    "CTRADER_CLIENT_SECRET": "test-secret",
    "CTRADER_ENVIRONMENT": "demo",
}


def _parse_structured(raw) -> dict:
    """Extract structured_content from a CallToolResult."""
    if hasattr(raw, "structured_content") and raw.structured_content is not None:
        return raw.structured_content
    if hasattr(raw, "data") and raw.data is not None:
        return raw.data
    return {}


@pytest.mark.asyncio
async def test_wraps_structured_result():
    """Structured dict results get wrapped under the envelope."""
    server = FastMCP("test")
    server.add_middleware(TrustBoundaryMiddleware())

    @server.tool()
    async def echo_tool(msg: str) -> dict:
        return {"message": msg}

    async with Client(transport=server) as client:
        raw = await client.call_tool("echo_tool", {"msg": "hello"})

    result = _parse_structured(raw)
    assert SECURITY_KEY in result
    assert result[SECURITY_KEY]["trust"] == "untrusted_tool_output"
    assert result[SECURITY_KEY]["tool_name"] == "echo_tool"
    assert result[SECURITY_KEY]["risk"] == "api_structured"
    assert result[SECURITY_KEY]["instructions"] == INSTRUCTIONS["api_structured"]
    assert DATA_KEY in result
    assert result[DATA_KEY]["message"] == "hello"


@pytest.mark.asyncio
async def test_does_not_double_wrap():
    """If the result already contains the security key, skip wrapping."""
    server = FastMCP("test")
    server.add_middleware(TrustBoundaryMiddleware())

    @server.tool()
    async def pre_wrapped_tool() -> dict:
        return {
            SECURITY_KEY: {
                "trust": "untrusted_tool_output",
                "tool_name": "pre_wrapped_tool",
                "instructions": "already wrapped",
            },
            DATA_KEY: {"inner": "value"},
        }

    async with Client(transport=server) as client:
        raw = await client.call_tool("pre_wrapped_tool", {})

    result = _parse_structured(raw)
    assert result[SECURITY_KEY]["instructions"] == "already wrapped"
    assert result[DATA_KEY] == {"inner": "value"}


@pytest.mark.asyncio
async def test_meta_contains_wrapped_marker():
    """The result meta should contain the wrapped marker."""
    server = FastMCP("test")
    server.add_middleware(TrustBoundaryMiddleware())

    @server.tool()
    async def simple_tool() -> dict:
        return {"ok": True}

    async with Client(transport=server) as client:
        raw = await client.call_tool("simple_tool", {})

    if hasattr(raw, "meta") and raw.meta is not None:
        assert raw.meta.get(WRAPPED_MARKER) is True


def test_redact_secrets_in_dict():
    """Secrets in dicts should be redacted."""
    data = {
        "clientId": "my-client-id",
        "clientSecret": "super-secret-value",
        "accessToken": "my-access-token",
        "refreshToken": "my-refresh-token",
        "nested": {
            "access_token": "nested-token",
            "safe_field": "visible",
        },
    }
    redacted = redact_secrets(data)
    assert redacted["clientSecret"] == "[REDACTED]"
    assert redacted["accessToken"] == "[REDACTED]"
    assert redacted["refreshToken"] == "[REDACTED]"
    assert redacted["clientId"] == "my-client-id"
    assert redacted["nested"]["access_token"] == "[REDACTED]"
    assert redacted["nested"]["safe_field"] == "visible"


def test_redact_secrets_in_string():
    """Secrets in strings should be redacted."""
    text = '{"clientSecret": "secret123", "name": "test"}'
    redacted = redact_secrets(text)
    assert "secret123" not in redacted
    assert "[REDACTED]" in redacted
    assert '"name": "test"' in redacted


def test_redact_secrets_in_list():
    """Secrets in lists should be redacted."""
    data = [
        {"clientSecret": "secret1"},
        {"safe": "value"},
    ]
    redacted = redact_secrets(data)
    assert redacted[0]["clientSecret"] == "[REDACTED]"
    assert redacted[1]["safe"] == "value"


def test_sanitize_for_log():
    """Log messages should have secrets sanitized."""
    message = "Token response: clientSecret=abc123&accessToken=xyz789"
    sanitized = sanitize_for_log(message)
    assert "abc123" not in sanitized
    assert "xyz789" not in sanitized
    assert "[REDACTED]" in sanitized


def test_sanitize_for_log_json():
    """JSON log messages should have secrets sanitized."""
    message = '{"clientSecret": "my-secret", "status": "ok"}'
    sanitized = sanitize_for_log(message)
    assert "my-secret" not in sanitized
    assert "[REDACTED]" in sanitized
