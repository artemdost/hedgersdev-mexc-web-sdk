"""WebSocket client for the MEXC futures stream (``wss://contract.mexc.com/edge``).

Public channels need no auth; private channels (personal orders / positions /
assets) require a login with either the web token or an API key. A background
thread pumps messages to your ``on_message`` callback and a keep-alive ping is
sent every 15s.

Requires the optional ``websocket-client`` dependency::

    pip install "mexc-web[ws]"
"""

from __future__ import annotations

import hashlib
import hmac
import json
import threading
from time import time
from typing import Any, Callable

try:
    import websocket  # type: ignore
except ImportError:  # pragma: no cover
    websocket = None  # noqa: N816

__all__ = ["MexcWSClient"]

_WS_URL = "https://contract.mexc.com/edge".replace("https", "wss")

MessageHandler = Callable[[dict[str, Any]], None]


class MexcWSClient:
    """Threaded WebSocket client for MEXC futures.

    Example::

        def on_msg(msg):
            print(msg.get("channel"), msg.get("data"))

        ws = MexcWSClient(on_message=on_msg)
        ws.connect()
        ws.sub_deal("BTC_USDT")
        ws.sub_depth("BTC_USDT")
        # ... later
        ws.close()

    For private streams pass a ``token`` (web ``u_id``) or ``api_key`` +
    ``api_secret``; login is sent automatically on connect.
    """

    def __init__(
        self,
        on_message: MessageHandler,
        *,
        token: str | None = None,
        api_key: str | None = None,
        api_secret: str | None = None,
        on_open: Callable[[], None] | None = None,
        on_close: Callable[[], None] | None = None,
        on_error: Callable[[Exception], None] | None = None,
        ping_interval: float = 15.0,
    ) -> None:
        if websocket is None:
            raise ImportError(
                "websocket-client is required for MexcWSClient; install with "
                "'pip install \"mexc-web[ws]\"'"
            )
        self._on_message = on_message
        self._token = token
        self._api_key = api_key
        self._api_secret = api_secret
        self._on_open = on_open
        self._on_close = on_close
        self._on_error = on_error
        self._ping_interval = ping_interval

        self._ws: Any = None
        self._thread: threading.Thread | None = None
        self._ping_thread: threading.Thread | None = None
        self._running = False
        self._pending: list[dict[str, Any]] = []

    # -- lifecycle ------------------------------------------------------

    def connect(self, *, block: bool = False) -> None:
        """Open the connection. Runs in a background thread unless ``block``."""
        self._ws = websocket.WebSocketApp(
            _WS_URL,
            on_open=self._handle_open,
            on_message=self._handle_message,
            on_close=self._handle_close,
            on_error=self._handle_error,
        )
        self._running = True
        if block:
            self._ws.run_forever()
        else:
            self._thread = threading.Thread(target=self._ws.run_forever, daemon=True)
            self._thread.start()

    def close(self) -> None:
        self._running = False
        if self._ws is not None:
            self._ws.close()

    # -- auth -----------------------------------------------------------

    def _login_message(self) -> dict[str, Any] | None:
        if self._token:
            return {"method": "login", "param": {"token": self._token}}
        if self._api_key and self._api_secret:
            req_time = str(int(time() * 1000))
            sign = hmac.new(
                self._api_secret.encode(),
                f"{self._api_key}{req_time}".encode(),
                hashlib.sha256,
            ).hexdigest()
            return {
                "method": "login",
                "param": {"apiKey": self._api_key, "reqTime": req_time, "signature": sign},
            }
        return None

    # -- subscriptions --------------------------------------------------

    def send(self, message: dict[str, Any]) -> None:
        """Send a raw command dict (queued until the socket is open)."""
        if self._ws is not None and self._ws.sock and self._ws.sock.connected:
            self._ws.send(json.dumps(message))
        else:
            self._pending.append(message)

    def subscribe(self, method: str, param: dict[str, Any] | None = None) -> None:
        """Generic subscribe, e.g. ``subscribe("sub.depth", {"symbol": "BTC_USDT"})``."""
        self.send({"method": method, "param": param or {}})

    def unsubscribe(self, method: str, param: dict[str, Any] | None = None) -> None:
        """Generic unsubscribe, e.g. ``unsubscribe("unsub.depth", {"symbol": "BTC_USDT"})``.

        Accepts either the ``sub.*`` or ``unsub.*`` form for convenience.
        """
        if method.startswith("sub."):
            method = "un" + method
        self.send({"method": method, "param": param or {}})

    def sub_depth(self, symbol: str, *, limit: int | None = None) -> None:
        param: dict[str, Any] = {"symbol": symbol}
        if limit is not None:
            param["limit"] = limit
        self.subscribe("sub.depth", param)

    def sub_depth_step(self, symbol: str, *, step: int | None = None, **param: Any) -> None:
        """Depth aggregated to a minimum notional step. ``sub.depth.step``."""
        p: dict[str, Any] = {"symbol": symbol, **param}
        if step is not None:
            p["step"] = step
        self.subscribe("sub.depth.step", p)

    def sub_deal(self, symbol: str) -> None:
        self.subscribe("sub.deal", {"symbol": symbol})

    def sub_ticker(self, symbol: str) -> None:
        self.subscribe("sub.ticker", {"symbol": symbol})

    def sub_tickers(self) -> None:
        self.subscribe("sub.tickers", {})

    def sub_kline(self, symbol: str, interval: str = "Min1") -> None:
        self.subscribe("sub.kline", {"symbol": symbol, "interval": interval})

    def sub_funding_rate(self, symbol: str) -> None:
        self.subscribe("sub.funding.rate", {"symbol": symbol})

    def sub_index_price(self, symbol: str) -> None:
        self.subscribe("sub.index.price", {"symbol": symbol})

    def sub_fair_price(self, symbol: str) -> None:
        self.subscribe("sub.fair.price", {"symbol": symbol})

    def sub_contract(self, symbol: str) -> None:
        """Contract-info stream. ``sub.contract``."""
        self.subscribe("sub.contract", {"symbol": symbol})

    def sub_event_contract(self, symbol: str) -> None:
        """Event-contract stream. ``sub.event.contract``."""
        self.subscribe("sub.event.contract", {"symbol": symbol})

    #: Valid private-push filter names for :meth:`personal_filter`.
    FILTERS = (
        "order",
        "order.deal",
        "position",
        "plan.order",
        "stop.order",
        "stop.planorder",
        "risk.limit",
        "adl.level",
        "asset",
    )

    def personal_filter(self, filters: list[str]) -> None:
        """Restrict private pushes to the given filters.

        Valid names (see :attr:`FILTERS`): order, order.deal, position,
        plan.order, stop.order, stop.planorder, risk.limit, adl.level, asset.
        Example: ``ws.personal_filter(["order", "position", "asset"])``.
        """
        self.subscribe(
            "personal.filter", {"filters": [{"filter": f} for f in filters]}
        )

    # -- internal handlers ---------------------------------------------

    def _handle_open(self, _ws: Any) -> None:
        login = self._login_message()
        if login is not None:
            self._ws.send(json.dumps(login))
        for msg in self._pending:
            self._ws.send(json.dumps(msg))
        self._pending.clear()
        self._start_ping()
        if self._on_open:
            self._on_open()

    def _handle_message(self, _ws: Any, raw: str) -> None:
        try:
            msg = json.loads(raw)
        except ValueError:
            return
        # swallow pong keep-alives
        if msg.get("channel") == "pong":
            return
        self._on_message(msg)

    def _handle_close(self, _ws: Any, *_args: Any) -> None:
        self._running = False
        if self._on_close:
            self._on_close()

    def _handle_error(self, _ws: Any, err: Exception) -> None:
        if self._on_error:
            self._on_error(err)

    def _start_ping(self) -> None:
        def loop() -> None:
            while self._running and self._ws is not None:
                try:
                    if self._ws.sock and self._ws.sock.connected:
                        self._ws.send(json.dumps({"method": "ping"}))
                except Exception:  # noqa: BLE001
                    break
                # sleep in small steps so close() is responsive
                waited = 0.0
                while self._running and waited < self._ping_interval:
                    threading.Event().wait(0.5)
                    waited += 0.5

        self._ping_thread = threading.Thread(target=loop, daemon=True)
        self._ping_thread.start()
