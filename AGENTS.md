# Agent Instructions — ctrader-mcp-server

Standalone MCP server for the cTrader Open API, built on `ctrader-open-api`
(Twisted/protobuf client) and FastMCP. This is **not** a fork of, and does not
reference, any other MCP server.

## Architecture

- `session.py` — adapts `ctrader_open_api` behind an async session manager
  (TLS lifecycle, app/account auth, request correlation, reconnects, streaming cache).
- `oauth.py` — local OAuth authorization-code flow against `openapi.ctrader.com`.
- `config.py` — env-driven configuration.
- `security.py` — trust-boundary middleware wrapping every tool result.
- `tool_registry.py` / `toolsets.py` — curated tool definitions and namespace filtering.
- `tools/*` — hand-written tool groups (auth, account, trading, market_data,
  streaming, diagnostics).

## Tests

Three layers, no network required except opt-in integration:

```bash
pytest tests/ -q                                  # core (39+ tests)
pytest tests/ -m integration -v                   # requires real credentials
```

## Conventions

- Tools return plain dicts; errors use `{"error": {"message": ...}}`.
- Never expose `client_secret`, tokens, or URLs containing tokens in responses or logs.
- One cTrader account per process; account IDs come from config, not tool args.
- `ctrader-open-api` is pinned; bump deliberately.
