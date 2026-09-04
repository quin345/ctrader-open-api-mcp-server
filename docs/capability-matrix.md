# cTrader MCP Server — Capability Matrix

This document maps every cTrader Open API request, response, event, and
major model to its MCP tool equivalent, or notes the absence of one.

## Legend

| Marker | Meaning |
|--------|---------|
| `DIRECT` | Mapped to a curated MCP tool with similar semantics |
| `PARTIAL` | Mapped to a tool with adapted/different semantics |
| `NO-EQUIVALENCE` | Intentionally not provided by this server |
| `CTRADER-ONLY` | cTrader capability exposed as an internal/housekeeping tool |

---

## Authentication & Connection

| cTrader Message / Concept | MCP Tool | Mapping |
|---------------------------|----------|---------|
| `ProtoOAApplicationAuthReq/Res` | `auth` group (internal) | CTRADER-ONLY |
| `ProtoOAAccountAuthReq/Res` | `auth` group (internal) | CTRADER-ONLY |
| `ProtoOAGetAccountListByAuthReq/Res` | `discover_accounts` (internal) | CTRADER-ONLY |
| OAuth authorization-code flow | `get_authorization_url`, `exchange_authorization_code` | CTRADER-ONLY |
| Refresh-token rotation | `refresh_access_token` | CTRADER-ONLY |
| `ProtoOAVersionReq/Res` | `get_protocol_version` | CTRADER-ONLY |
| `ProtoOAClientDisconnectEvent` | (handled internally) | CTRADER-ONLY |
| `ProtoOAAccountDisconnectEvent` | (handled internally) | CTRADER-ONLY |
| `ProtoOAAccountsTokenInvalidatedEvent` | (handled internally) | CTRADER-ONLY |

## Account & Trader State

| cTrader Message / Concept | MCP Tool | Mapping |
|---------------------------|----------|---------|
| `ProtoOATraderReq/Res` | `get_trader_info` | PARTIAL |
| `ProtoOAAssetListReq/Res` | `get_account_assets` | PARTIAL |
| `ProtoOAAssetClassListReq/Res` | `get_account_asset_classes` | PARTIAL |
| `ProtoOACashFlowHistoryReq/Res` | `get_cash_flow_history` | PARTIAL |
| `ProtoOAGetPositionUnrealizedPnLReq/Res` | `get_unrealized_pnl` | PARTIAL |
| `ProtoOAMarginCallListReq/Res` | `get_margin_call_status` | PARTIAL |
| `ProtoOAMarginCallUpdateReq/Res` | (handled internally) | CTRADER-ONLY |
| `ProtoOAMarginCallUpdateEvent` | (handled internally) | CTRADER-ONLY |
| `ProtoOAMarginCallTriggerEvent` | (handled internally) | CTRADER-ONLY |
| `ProtoOAExpectedMarginReq/Res` | `get_expected_margin` | PARTIAL |
| `ProtoOADynamicLeverageListReq/Res` | `get_dynamic_leverage` | CTRADER-ONLY |


## Trading: Orders

| cTrader Message / Concept | MCP Tool | Mapping |
|---------------------------|----------|---------|
| `ProtoOANewOrderReq` (market) | `place_market_order` | DIRECT |
| `ProtoOANewOrderReq` (limit) | `place_limit_order` | DIRECT |
| `ProtoOANewOrderReq` (stop) | `place_stop_order` | DIRECT |
| `ProtoOAAmendOrderReq` | `amend_order` | DIRECT |
| `ProtoOACancelOrderReq` | `cancel_order` | DIRECT |
| `ProtoOAOrderListReq/Res` | `get_orders` | DIRECT |
| `ProtoOAOrderDetailsReq/Res` | `get_order_by_id` | DIRECT |
| `ProtoOAExecutionEvent` | (handled internally) | CTRADER-ONLY |

## Trading: Positions & Deals

| cTrader Message / Concept | MCP Tool | Mapping |
|---------------------------|----------|---------|
| `ProtoOAPositionListReq/Res` | `get_positions` | DIRECT |
| `ProtoOAClosePositionReq/Res` | `close_position` | DIRECT |
| Close all positions | `close_all_positions` | DIRECT |
| `ProtoOADealListReq/Res` | `get_deals` | DIRECT |
| `ProtoOADealListByPositionIdReq/Res` | `get_deals_by_position` | DIRECT |

## Market Data: Symbols & Historical

| cTrader Message / Concept | MCP Tool | Mapping |
|---------------------------|----------|---------|
| `ProtoOASymbolListReq/Res` | `get_symbols` | DIRECT |
| `ProtoOASymbolByIdReq/Res` | `get_symbol_by_id` | DIRECT |
| Conversion symbols | `get_conversion_symbols` | CTRADER-ONLY |
| `ProtoOAGetTrendbarsReq/Res` | `get_trendbars` | PARTIAL |
| `ProtoOAGetTickDataReq/Res` | `get_tick_data` | PARTIAL |

## Market Data: Streaming

| cTrader Message / Concept | MCP Tool | Mapping |
|---------------------------|----------|---------|
| `ProtoOASubscribeForSpotQuotesReq/Res` | `subscribe_spots` | DIRECT |
| `ProtoOAUnsubscribeForSpotQuotesReq/Res` | `unsubscribe_spots` | DIRECT |
| `ProtoOASpotEvent` | `poll_spots` | DIRECT |
| `ProtoOASubscribeForTrendbarsReq/Res` | `subscribe_trendbars` | DIRECT |
| `ProtoOAUnsubscribeForTrendbarsReq/Res` | `unsubscribe_trendbars` | DIRECT |
| `ProtoOASubscribeDepthQuotesReq/Res` | `subscribe_depth` | DIRECT |
| `ProtoOAUnsubscribeDepthQuotesReq/Res` | `unsubscribe_depth` | DIRECT |
| `ProtoOADepthEvent` | `poll_depth` | DIRECT |

## Intentionally Not Provided

- News feeds, corporate actions, fixed-income quotes
- Options contracts, chains, Greeks, and exercise
- Market movers, watchlists, short-sale locates
- Third-party account configuration endpoints
- Exchange calendar / clock semantics (cTrader does not expose these)
- US-equity/SIP/IEX-style market-data semantics (cTrader is a CFD/FX protocol)
