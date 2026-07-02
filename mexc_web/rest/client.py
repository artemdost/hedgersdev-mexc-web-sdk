"""Top-level synchronous MEXC futures client (web-token auth)."""

from __future__ import annotations

from typing import Any

import requests

from .._internal.transport import Transport
from .account import AccountAPI
from .market import MarketAPI
from .orders import OrdersAPI
from .plan import PlanOrdersAPI
from .positions import PositionsAPI
from .stp import StpAPI
from .tpsl import TpslAPI
from .trailing import TrailingAPI

__all__ = ["MexcClient"]


class MexcClient:
    """Synchronous MEXC futures client authenticated with the web (``u_id``) token.

    Grab the token from your browser: log in at mexc.com, open DevTools →
    Application → Cookies → ``https://www.mexc.com`` → copy the ``u_id`` value.
    Tokens expire after ~1-4 weeks; refresh when calls start returning auth
    errors.

    Endpoints are grouped into namespaces::

        client.market      # public market data (no token needed)
        client.account     # balances, fees, risk limits
        client.positions   # positions, leverage, margin, position mode
        client.orders      # place / cancel / query orders, batch, chase
        client.plan        # conditional (plan) orders
        client.tpsl        # take-profit / stop-loss orders
        client.trailing    # trailing-stop orders
        client.stp         # self-trade-prevention groups

    Example::

        from mexc_web import MexcClient

        client = MexcClient("YOUR_U_ID_TOKEN")
        print(client.account.assets())
        client.orders.create("BTC_USDT", side=1, vol=1, price=50000, leverage=20)
    """

    def __init__(
        self,
        token: str | None = None,
        *,
        base_url: str = "https://futures.mexc.com/api/v1",
        timeout: float = 10.0,
        session: requests.Session | None = None,
    ) -> None:
        self._transport = Transport(
            token, base_url=base_url, timeout=timeout, session=session
        )
        self.market = MarketAPI(self._transport)
        self.account = AccountAPI(self._transport)
        self.positions = PositionsAPI(self._transport)
        self.orders = OrdersAPI(self._transport)
        self.plan = PlanOrdersAPI(self._transport)
        self.tpsl = TpslAPI(self._transport)
        self.trailing = TrailingAPI(self._transport)
        self.stp = StpAPI(self._transport)

    # -- token / lifecycle ---------------------------------------------

    @property
    def token(self) -> str | None:
        return self._transport.token

    def set_token(self, token: str) -> None:
        """Replace the web token (after refreshing it from the browser)."""
        self._transport.set_token(token)

    def request(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, Any] | list[Any] | None = None,
        auth: bool = True,
    ) -> Any:
        """Escape hatch for any endpoint not wrapped above.

        ``path`` is relative to the base URL, e.g. ``/private/account/assets``.
        """
        return self._transport.request(method, path, params=params, auth=auth)

    def close(self) -> None:
        self._transport.close()

    def __enter__(self) -> "MexcClient":
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()
