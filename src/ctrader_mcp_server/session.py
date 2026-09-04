"""
cTrader session manager.

Adapts the cTrader Twisted/protobuf client behind an async session
abstraction suitable for use with FastMCP tools.
"""

from __future__ import annotations

import asyncio
import logging
from collections import deque
from dataclasses import dataclass, field
from typing import Any, Optional

from .config import ServerConfig
from .oauth import OAuthManager

logger = logging.getLogger(__name__)


@dataclass
class ConnectionState:
    """Tracks the current state of the cTrader connection."""

    connected: bool = False
    application_authenticated: bool = False
    account_authenticated: bool = False
    account_id: str = ""
    protocol_version: str = ""
    reconnect_attempts: int = 0
    last_error: str = ""


@dataclass
class StreamingCache:
    """Bounded cache for streaming events."""

    max_size: int = 1000
    _spots: dict[str, deque[dict]] = field(default_factory=dict)
    _trendbars: dict[str, deque[dict]] = field(default_factory=dict)
    _depth: dict[str, deque[dict]] = field(default_factory=dict)

    def add_spot(self, symbol: str, event: dict) -> None:
        if symbol not in self._spots:
            self._spots[symbol] = deque(maxlen=self.max_size)
        self._spots[symbol].append(event)

    def add_trendbar(self, symbol: str, event: dict) -> None:
        if symbol not in self._trendbars:
            self._trendbars[symbol] = deque(maxlen=self.max_size)
        self._trendbars[symbol].append(event)

    def add_depth(self, symbol: str, event: dict) -> None:
        if symbol not in self._depth:
            self._depth[symbol] = deque(maxlen=self.max_size)
        self._depth[symbol].append(event)

    def poll_spots(self, symbol: str) -> list[dict]:
        events = list(self._spots.get(symbol, []))
        self._spots.get(symbol, deque()).clear()
        return events

    def poll_trendbars(self, symbol: str) -> list[dict]:
        events = list(self._trendbars.get(symbol, []))
        self._trendbars.get(symbol, deque()).clear()
        return events

    def poll_depth(self, symbol: str) -> list[dict]:
        events = list(self._depth.get(symbol, []))
        self._depth.get(symbol, deque()).clear()
        return events

    def clear(self) -> None:
        self._spots.clear()
        self._trendbars.clear()
        self._depth.clear()


class SessionError(Exception):
    """Raised when a session operation fails."""
    pass

class CTraderSession:
    """Manages a cTrader Open API session."""

    def __init__(self, config: ServerConfig, oauth: OAuthManager = None):
        self._config = config
        self._oauth = oauth
        self._state = ConnectionState()
        self._streaming_cache = StreamingCache()
        self._client: Any = None
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._pending_responses: dict[str, asyncio.Future] = {}

    @property
    def state(self) -> ConnectionState:
        return self._state

    @property
    def streaming_cache(self) -> StreamingCache:
        return self._streaming_cache

    async def connect(self) -> None:
        """Establish a TLS connection to the cTrader backend."""
        try:
            from twisted.internet import reactor
            from ctrader_open_api.client import Client
            from ctrader_open_api.tcpProtocol import TcpProtocol
        except ImportError:
            raise RuntimeError("ctrader-open-api package is required.")

        self._loop = asyncio.get_event_loop()
        host = self._config.get_host()
        port = self._config.get_port()

        self._client = Client(host, port, TcpProtocol)
        self._client.setConnectedCallback(lambda c: self._on_connected())
        self._client.setDisconnectedCallback(
            lambda c, reason: self._on_disconnected(reason)
        )
        self._client.setMessageReceivedCallback(
            lambda c, msg: self._on_message_received(msg)
        )
        self._client.startService()

        # Wait for the connection to be established
        for _ in range(self._config.request_timeout):
            if self._state.connected:
                break
            await asyncio.sleep(0.1)
        else:
            raise SessionError("Failed to connect to cTrader backend.")

        # Auto-authenticate application
        await self.authenticate_application()

        # Auto-authenticate account if configured
        account_id = self._config.account_id or self._state.account_id
        if account_id:
            await self.authenticate_account(account_id)

    async def disconnect(self) -> None:
        """Disconnect from the cTrader backend."""
        if self._client is not None:
            self._client.stopService()
            self._client = None
        self._state.connected = False
        self._state.application_authenticated = False
        self._state.account_authenticated = False
        self._streaming_cache.clear()

    async def authenticate_application(self) -> dict:
        """Send application authentication request.

        When ``client_id`` and ``client_secret`` are configured (OAuth
        flow), sends ``ProtoOAApplicationAuthReq``.  Otherwise, skips app
        auth and just marks the application as authenticated (the access
        token alone is sufficient for account-level auth).
        """
        if not self._state.connected:
            raise SessionError("Not connected. Call connect() first.")

        if self._config.client_id and self._config.client_secret:
            from ctrader_open_api.messages.OpenApiMessages_pb2 import (
                ProtoOAApplicationAuthReq,
            )

            request = ProtoOAApplicationAuthReq()
            request.clientId = self._config.client_id
            request.clientSecret = self._config.client_secret
            await self._send_request(request)
        else:
            logger.debug(
                "Skipping application auth (no client_id/secret); "
                "using access token directly."
            )

        self._state.application_authenticated = True
        return {"status": "authenticated"}

    def _get_access_token(self) -> str:
        """Return the access token from OAuthManager or config."""
        if self._oauth is not None:
            token = self._oauth.access_token
            if token:
                return token
        return self._config.access_token

    async def discover_accounts(self) -> list[dict]:
        """Discover available trading accounts using the OAuth access token."""
        if not self._state.application_authenticated:
            raise SessionError("Application not authenticated.")

        from ctrader_open_api.messages.OpenApiMessages_pb2 import (
            ProtoOAGetAccountListByAuthReq,
        )

        access_token = self._get_access_token()
        if not access_token:
            raise SessionError("No access token available.")

        request = ProtoOAGetAccountListByAuthReq()
        request.accessToken = access_token

        response = await self._send_request(request)
        accounts = []
        for account in response.ctidTraderAccount:
            accounts.append({
                "ctidTraderAccountId": account.ctidTraderAccountId,
                "traderLogin": getattr(account, "traderLogin", ""),
            })
        return accounts

    async def authenticate_account(self, account_id: str) -> dict:
        """Authenticate a specific trading account."""
        if not self._state.application_authenticated:
            raise SessionError("Application not authenticated.")

        from ctrader_open_api.messages.OpenApiMessages_pb2 import (
            ProtoOAAccountAuthReq,
        )

        access_token = self._get_access_token()
        if not access_token:
            raise SessionError("No access token available.")

        request = ProtoOAAccountAuthReq()
        request.ctidTraderAccountId = int(account_id)
        request.accessToken = access_token

        await self._send_request(request)
        self._state.account_authenticated = True
        self._state.account_id = account_id
        return {"status": "account_authenticated", "accountId": account_id}

    async def get_protocol_version(self) -> str:
        """Get the cTrader Open API protocol version."""
        if not self._state.connected:
            raise SessionError("Not connected.")

        from ctrader_open_api.messages.OpenApiMessages_pb2 import (
            ProtoOAVersionReq,
        )

        request = ProtoOAVersionReq()
        response = await self._send_request(request)
        self._state.protocol_version = response.version
        return response.version

    async def get_trader_info(self, account_id: str = "") -> dict:
        """Get trader information for the selected account."""
        self._ensure_account_auth(account_id)

        from ctrader_open_api.messages.OpenApiMessages_pb2 import (
            ProtoOATraderReq,
        )

        request = ProtoOATraderReq()
        request.ctidTraderAccountId = int(account_id or self._state.account_id)

        response = await self._send_request(request)
        trader = response.trader
        return {
            "ctidTraderAccountId": trader.ctidTraderAccountId,
            "balance": trader.balance,
            "equity": getattr(trader, "equity", 0),
            "margin": getattr(trader, "margin", 0),
            "freeMargin": getattr(trader, "freeMargin", 0),
            "leverage": getattr(trader, "leverage", 0),
            "marginLevel": getattr(trader, "marginLevel", 0),
        }

    async def get_positions(self, account_id: str = "") -> list[dict]:
        """Get all open positions for the selected account."""
        self._ensure_account_auth(account_id)

        from ctrader_open_api.messages.OpenApiMessages_pb2 import (
            ProtoOAPositionListReq,
        )

        request = ProtoOAPositionListReq()
        request.ctidTraderAccountId = int(account_id or self._state.account_id)

        response = await self._send_request(request)
        positions = []
        for pos in response.position:
            positions.append({
                "positionId": pos.positionId,
                "symbolId": pos.tradeData.symbolId,
                "tradeSide": str(pos.tradeData.tradeSide),
                "volume": pos.tradeData.volume,
                "price": getattr(pos, "price", 0),
                "unrealizedPnL": getattr(pos, "unrealizedPnL", 0),
            })
        return positions

    async def get_orders(self, account_id: str = "") -> list[dict]:
        """Get all pending orders for the selected account."""
        self._ensure_account_auth(account_id)

        from ctrader_open_api.messages.OpenApiMessages_pb2 import (
            ProtoOAOrderListReq,
        )

        request = ProtoOAOrderListReq()
        request.ctidTraderAccountId = int(account_id or self._state.account_id)

        response = await self._send_request(request)
        orders = []
        for order in response.order:
            orders.append({
                "orderId": order.orderId,
                "symbolId": order.tradeData.symbolId,
                "tradeSide": str(order.tradeData.tradeSide),
                "volume": order.tradeData.volume,
                "orderType": str(order.tradeData.orderType),
                "limitPrice": getattr(order, "limitPrice", 0),
                "stopPrice": getattr(order, "stopPrice", 0),
                "orderStatus": str(getattr(order, "orderStatus", "")),
            })
        return orders

    async def place_order(
        self,
        symbol_id: int,
        trade_side: str,
        volume: int,
        order_type: str = "MARKET",
        limit_price: float = 0,
        stop_price: float = 0,
        account_id: str = "",
        client_order_id: str = "",
        stop_loss: float = 0,
        take_profit: float = 0,
    ) -> dict:
        """Place a new order on the selected account."""
        self._ensure_account_auth(account_id)

        from ctrader_open_api.messages.OpenApiMessages_pb2 import (
            ProtoOANewOrderReq,
        )
        from ctrader_open_api.messages.OpenApiModelMessages_pb2 import (
            ProtoOATradeSide,
            ProtoOAOrderType,
        )

        side_map = {"BUY": ProtoOATradeSide.BUY, "SELL": ProtoOATradeSide.SELL}
        type_map = {
            "MARKET": ProtoOAOrderType.MARKET,
            "LIMIT": ProtoOAOrderType.LIMIT,
            "STOP": ProtoOAOrderType.STOP,
        }

        request = ProtoOANewOrderReq()
        request.ctidTraderAccountId = int(account_id or self._state.account_id)
        request.symbolId = symbol_id
        request.tradeSide = side_map.get(trade_side.upper(), ProtoOATradeSide.BUY)
        request.orderType = type_map.get(order_type.upper(), ProtoOAOrderType.MARKET)
        request.volume = volume
        request.limitPrice = limit_price
        request.stopPrice = stop_price
        request.stopLoss = stop_loss
        request.takeProfit = take_profit
        if client_order_id:
            request.clientOrderId = client_order_id

        response = await self._send_request(request)
        return {
            "orderId": getattr(response, "orderId", 0),
            "clientOrderId": getattr(response, "clientOrderId", ""),
        }

    async def cancel_order(self, order_id: int, account_id: str = "") -> dict:
        """Cancel a pending order."""
        self._ensure_account_auth(account_id)

        from ctrader_open_api.messages.OpenApiMessages_pb2 import (
            ProtoOACancelOrderReq,
        )

        request = ProtoOACancelOrderReq()
        request.ctidTraderAccountId = int(account_id or self._state.account_id)
        request.orderId = order_id

        await self._send_request(request)
        return {"status": "cancelled", "orderId": order_id}

    async def close_position(
        self, position_id: int, volume: int = 0, account_id: str = "",
    ) -> dict:
        """Close an open position."""
        self._ensure_account_auth(account_id)

        from ctrader_open_api.messages.OpenApiMessages_pb2 import (
            ProtoOAClosePositionReq,
        )

        request = ProtoOAClosePositionReq()
        request.ctidTraderAccountId = int(account_id or self._state.account_id)
        request.positionId = position_id
        if volume > 0:
            request.volume = volume

        response = await self._send_request(request)
        return {
            "status": "closed",
            "positionId": position_id,
            "grossProfit": getattr(
                getattr(response, "closePositionDetail", None),
                "grossProfit", 0
            ),
        }

    async def get_symbols(self, account_id: str = "") -> list[dict]:
        """Get the list of tradable symbols for the selected account."""
        self._ensure_account_auth(account_id)

        from ctrader_open_api.messages.OpenApiMessages_pb2 import (
            ProtoOASymbolListReq,
        )

        request = ProtoOASymbolListReq()
        request.ctidTraderAccountId = int(account_id or self._state.account_id)

        response = await self._send_request(request)
        symbols = []
        for symbol in response.symbol:
            symbols.append({
                "symbolId": symbol.symbolId,
                "symbolName": getattr(symbol, "symbolName", ""),
                "digits": getattr(symbol, "digits", 0),
                "pipPosition": getattr(symbol, "pipPosition", 0),
                "enabled": getattr(symbol, "enabled", True),
            })
        return symbols

    async def get_trendbars(
        self,
        symbol_id: int,
        period: str = "M1",
        from_ts: int = 0,
        to_ts: int = 0,
        account_id: str = "",
    ) -> list[dict]:
        """Get historical trendbars for a symbol."""
        self._ensure_account_auth(account_id)

        from ctrader_open_api.messages.OpenApiMessages_pb2 import (
            ProtoOAGetTrendbarsReq,
        )
        from ctrader_open_api.messages.OpenApiModelMessages_pb2 import (
            ProtoOATrendbarPeriod,
        )

        period_map = {
            "M1": ProtoOATrendbarPeriod.M1,
            "M5": ProtoOATrendbarPeriod.M5,
            "M15": ProtoOATrendbarPeriod.M15,
            "M30": ProtoOATrendbarPeriod.M30,
            "H1": ProtoOATrendbarPeriod.H1,
            "H4": ProtoOATrendbarPeriod.H4,
            "D1": ProtoOATrendbarPeriod.D1,
            "W1": ProtoOATrendbarPeriod.W1,
            "MN1": ProtoOATrendbarPeriod.MN1,
        }

        request = ProtoOAGetTrendbarsReq()
        request.ctidTraderAccountId = int(account_id or self._state.account_id)
        request.symbolId = symbol_id
        request.period = period_map.get(period.upper(), ProtoOATrendbarPeriod.M1)
        request.fromTimestamp = from_ts
        request.toTimestamp = to_ts

        response = await self._send_request(request)
        bars = []
        for bar in response.trendbar:
            bars.append({
                "timestamp": getattr(bar, "timestamp", 0),
                "open": getattr(bar, "open", 0),
                "high": getattr(bar, "high", 0),
                "low": getattr(bar, "low", 0),
                "close": getattr(bar, "close", 0),
                "volume": getattr(bar, "volume", 0),
            })
        return bars

    async def subscribe_spots(
        self, symbol_ids: list[int], account_id: str = "",
    ) -> dict:
        """Subscribe to live spot price updates."""
        self._ensure_account_auth(account_id)

        from ctrader_open_api.messages.OpenApiMessages_pb2 import (
            ProtoOASubscribeForSpotQuotesReq,
        )

        request = ProtoOASubscribeForSpotQuotesReq()
        request.ctidTraderAccountId = int(account_id or self._state.account_id)
        for sid in symbol_ids:
            request.symbolId.append(sid)

        await self._send_request(request)
        return {"status": "subscribed", "symbolIds": symbol_ids}

    async def _send_request(self, request: Any) -> Any:
        """Send a protobuf request and await the correlated response."""
        if self._client is None:
            raise SessionError("Not connected.")

        import uuid
        client_msg_id = str(uuid.uuid4())

        loop = asyncio.get_event_loop()
        future: asyncio.Future = loop.create_future()
        self._pending_responses[client_msg_id] = future

        self._client.send(request, clientMsgId=client_msg_id)

        try:
            response = await asyncio.wait_for(
                future, timeout=self._config.request_timeout,
            )
            return response
        except asyncio.TimeoutError:
            self._pending_responses.pop(client_msg_id, None)
            raise SessionError(
                f"Request timed out after {self._config.request_timeout}s"
            )

    def _on_connected(self) -> None:
        """Callback when the Twisted client connects."""
        self._state.connected = True
        self._state.reconnect_attempts = 0
        logger.info("Connected to cTrader backend")

    def _on_disconnected(self, reason: str) -> None:
        """Callback when the Twisted client disconnects."""
        self._state.connected = False
        self._state.application_authenticated = False
        self._state.account_authenticated = False
        logger.warning("Disconnected from cTrader: %s", reason)

        for future in self._pending_responses.values():
            if not future.done():
                future.set_exception(SessionError("Disconnected"))
        self._pending_responses.clear()

    def _on_message_received(self, message: Any) -> None:
        """Callback when a message is received from the Twisted client."""
        client_msg_id = getattr(message, "clientMsgId", None)

        if client_msg_id and client_msg_id in self._pending_responses:
            future = self._pending_responses.pop(client_msg_id)
            if not future.done():
                loop = self._loop
                if loop is not None:
                    loop.call_soon_threadsafe(future.set_result, message)
        else:
            self._handle_unsolicited_event(message)

    def _handle_unsolicited_event(self, message: Any) -> None:
        """Handle unsolicited events (streaming data, errors, etc.)."""
        try:
            from ctrader_open_api.messages.OpenApiMessages_pb2 import (
                ProtoOASpotEvent,
                ProtoOAErrorEvent,
            )
            from ctrader_open_api.protobuf import Protobuf

            payload = Protobuf.extract(message)

            if isinstance(payload, ProtoOASpotEvent):
                self._streaming_cache.add_spot(
                    str(payload.symbolId),
                    {
                        "symbolId": payload.symbolId,
                        "bid": getattr(payload, "bid", 0),
                        "ask": getattr(payload, "ask", 0),
                    },
                )
            elif isinstance(payload, ProtoOAErrorEvent):
                logger.error(
                    "cTrader error event: %s - %s",
                    payload.errorCode,
                    payload.description,
                )
        except Exception as exc:
            logger.debug("Could not process unsolicited event: %s", exc)

    def _ensure_account_auth(self, account_id: str) -> None:
        """Ensure the account is authenticated before making requests."""
        if not self._state.connected:
            raise SessionError("Not connected. Call connect() first.")
        if not self._state.application_authenticated:
            raise SessionError("Application not authenticated.")
        if not self._state.account_authenticated:
            raise SessionError("Account not authenticated.")


    async def unsubscribe_spots(
        self, symbol_ids: list[int], account_id: str = "",
    ) -> dict:
        """Unsubscribe from live spot price updates."""
        self._ensure_account_auth(account_id)

        from ctrader_open_api.messages.OpenApiMessages_pb2 import (
            ProtoOAUnsubscribeForSpotQuotesReq,
        )

        request = ProtoOAUnsubscribeForSpotQuotesReq()
        request.ctidTraderAccountId = int(account_id or self._state.account_id)
        for sid in symbol_ids:
            request.symbolId.append(sid)

        await self._send_request(request)
        return {"status": "unsubscribed", "symbolIds": symbol_ids}

