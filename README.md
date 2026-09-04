# cTrader MCP Server

A standalone MCP server for the cTrader Open API, built directly on
`ctrader-open-api` (the Twisted/protobuf client) and FastMCP.

## Features

- **OAuth authorization-code flow** with refresh-token rotation
- **Account discovery** and account authentication
- **Trading**: market, limit, stop orders; amendments; cancellations
- **Position management**: close, partial close, close all
- **Historical data**: trendbars and tick data with relative lookback
- **Streaming**: live spot prices, trendbars, and market depth
- **Account info**: trader state, cash flow, margin, P/L, dynamic leverage
- **Diagnostics**: protocol version, connection status
- **Trust-boundary middleware**: all outputs wrapped in security envelope
- **Secret redaction**: credentials and tokens never exposed

## Installation

```bash
pip install -e ".[dev]"
```

## Configuration

Set these environment variables:

| Variable | Required | Description |
|----------|----------|-------------|
| `CTRADER_ACCESS_TOKEN` | Yes | cTrader OAuth access token |
| `CTRADER_ACCOUNT_ID` | No | Pre-select an account ID |
| `CTRADER_ENVIRONMENT` | No | `demo` (default) or `live` |
| `CTRADER_CLIENT_ID` | No | cTrader application client ID (for OAuth flow) |
| `CTRADER_CLIENT_SECRET` | No | cTrader application client secret (for OAuth flow) |
| `CTRADER_REDIRECT_URI` | No | OAuth redirect URI (default: `http://localhost:8080/callback`) |
| `CTRADER_TOKEN_PATH` | No | Path for token storage |
| `CTRADER_TOOLSETS` | No | Comma-separated toolset names (default: all) |
| `CTRADER_REQUEST_TIMEOUT` | No | Request timeout in seconds (default: 30) |

## Usage

### STDIO Transport (for MCP clients like Claude Desktop)

```bash
ctrader-mcp-server
```

### HTTP Transport

```bash
ctrader-mcp-server --transport streamable-http --host 127.0.0.1 --port 8000
```

### With Env File

```bash
ctrader-mcp-server --env-file .env
```

## Authentication

The MCP server only needs an **access token** and optionally an **account ID**
to connect to the cTrader trading server. You can obtain an access token
through the cTrader OAuth flow (using your client ID and secret), or via
any other method (e.g. the cTrader web dashboard).

If you provide `CTRADER_CLIENT_ID` and `CTRADER_CLIENT_SECRET` as well, the
server will use the full OAuth authorization-code flow with automatic
refresh-token rotation. If you only provide `CTRADER_ACCESS_TOKEN`, the
server will use it directly for account authentication.

### Authentication Flow (OAuth, optional)

When `CTRADER_CLIENT_ID` and `CTRADER_CLIENT_SECRET` are set, the server
supports the full OAuth authorization-code flow:

1. Call `get_authorization_url` to get the OAuth URL
2. Open the URL in a browser and authorize the application
3. cTrader redirects to your local callback with an authorization code
4. Call `exchange_authorization_code` with the code
5. Tokens are stored locally and refreshed automatically

When only `CTRADER_ACCESS_TOKEN` is set, this flow is skipped and the token
is used directly for account authentication.

## Tool Groups

| Group | Tools |
|-------|-------|
| `auth` | Authorization URL, code exchange, token refresh, status |
| `account` | Trader info, assets, cash flow, P/L, margin, leverage |
| `trading` | Orders, positions, deals, close |
| `market_data` | Symbols, trendbars, tick data |
| `streaming` | Subscribe/unsubscribe/poll spots, trendbars, depth |
| `diagnostics` | Protocol version, connection status |

## Demo vs Live

- **Demo**: Connects to `demo.ctraderapi.com:5035`
- **Live**: Connects to `live.ctraderapi.com:5035`

Set `CTRADER_ENVIRONMENT=live` for live trading. Use demo for development.

## Token Protection

- Tokens are stored in `~/.ctrader_mcp_server/tokens.json` by default
- File permissions are set to owner-read/write only (0o600)
- Tokens are never exposed in MCP responses, logs, or URLs
- Token values are redacted from all output

## Streaming Behavior

Streaming uses a bounded event cache with non-blocking polling:

1. Call `subscribe_spots` to start receiving spot price events
2. Events are buffered in a bounded cache (default: 1000 events per symbol)
3. Call `poll_spots` to retrieve buffered events (non-blocking)
4. Call `unsubscribe_spots` to stop receiving events

The same pattern applies to trendbars and market depth.

## Security

All tool outputs are wrapped in a trust-boundary envelope:

```json
{
  "_ctrader_mcp_security": {
    "trust": "untrusted_tool_output",
    "tool_name": "...",
    "risk": "api_structured",
    "instructions": "..."
  },
  "data": { ... }
}
```

This separates server-authored metadata from untrusted API data,
making the trust boundary visible to models.

## Capability Matrix

See [docs/capability-matrix.md](docs/capability-matrix.md) for a complete
mapping of cTrader protobuf messages to MCP tools.

## License

MIT
