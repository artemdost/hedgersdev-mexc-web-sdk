"""Spot OpenAPI client (API-key HMAC) — wallet balances and internal transfers.

This is a **separate** auth mechanism from the web token: MEXC's spot v3 API
(``api.mexc.com``) signs requests with an API key + secret (HMAC-SHA256), the
key goes in the ``X-MEXC-APIKEY`` header and the signature in the query string.

It's an API-key alternative for moving funds between wallets and for spot-only
features (deposit addresses). If you already use a web token, ``client.wallet``
does transfers without an API key; this client is here for API-key workflows.
Ported from the raskor bot's ``MexcSpotClient``.

The API key needs the **Transfer / Wallet** permission enabled
(https://www.mexc.com/user/openapi), otherwise transfers return error 700007.
"""

from __future__ import annotations

import hashlib
import hmac
from time import time
from typing import Any
from urllib.parse import quote

import requests

from .._internal.errors import MexcAPIError, MexcHTTPError

__all__ = ["MexcSpotClient"]

# Account types accepted by /capital/transfer
SPOT = "SPOT"
FUTURES = "FUTURES"
MARGIN = "MARGIN"
#: Funding wallet (where fiat/card purchases land). MEXC's enum is "FUND";
#: if the API rejects it, try "FUNDING".
FUND = "FUND"


class MexcSpotClient:
    """Synchronous MEXC spot client for balances and internal transfers.

    Example::

        from mexc_web import MexcSpotClient

        spot = MexcSpotClient(api_key, api_secret)
        print(spot.balance("USDT"))
        spot.transfer_to_futures(25, "USDT")     # SPOT -> FUTURES
    """

    BASE_URL = "https://api.mexc.com"

    def __init__(
        self,
        api_key: str,
        api_secret: str,
        *,
        base_url: str = BASE_URL,
        timeout: float = 10.0,
        recv_window: int | None = None,
        session: requests.Session | None = None,
    ) -> None:
        self._key = api_key
        self._secret = api_secret
        self._base = base_url.rstrip("/")
        self._timeout = timeout
        self._recv_window = recv_window
        self._session = session or requests.Session()

    # -- signing / transport -------------------------------------------

    def _sign(self, query_string: str) -> str:
        return hmac.new(
            self._secret.encode(), query_string.encode(), hashlib.sha256
        ).hexdigest()

    def _request(self, method: str, path: str, params: dict[str, Any] | None = None) -> Any:
        params = {k: v for k, v in (params or {}).items() if v is not None}
        params["timestamp"] = int(time() * 1000)
        if self._recv_window is not None:
            params["recvWindow"] = self._recv_window
        # Sign the exact query string we send (values URL-encoded).
        qs = "&".join(
            f"{k}={quote(str(v), safe='')}" for k, v in sorted(params.items())
        )
        sig = self._sign(qs)
        url = f"{self._base}{path}?{qs}&signature={sig}"
        headers = {"X-MEXC-APIKEY": self._key, "Content-Type": "application/json"}

        resp = self._session.request(method, url, headers=headers, timeout=self._timeout)
        if not resp.ok:
            # Spot errors come back as {"code": ..., "msg": ...}
            try:
                body = resp.json()
            except ValueError:
                raise MexcHTTPError(resp.status_code, resp.text)
            raise MexcAPIError(
                body.get("code"), str(body.get("msg") or "spot request failed"), body
            )
        try:
            return resp.json()
        except ValueError:
            raise MexcHTTPError(resp.status_code, resp.text)

    def close(self) -> None:
        self._session.close()

    def __enter__(self) -> "MexcSpotClient":
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()

    # -- account / balances --------------------------------------------

    def account(self) -> Any:
        """Full spot account. ``GET /api/v3/account``."""
        return self._request("GET", "/api/v3/account")

    def balances(self) -> list[dict[str, Any]]:
        """Non-zero spot balances as ``[{asset, free, locked, total}, ...]``."""
        data = self.account()
        out: list[dict[str, Any]] = []
        for b in data.get("balances", []):
            free = float(b.get("free", 0) or 0)
            locked = float(b.get("locked", 0) or 0)
            if free or locked:
                out.append(
                    {"asset": b.get("asset"), "free": free, "locked": locked, "total": free + locked}
                )
        return out

    def balance(self, asset: str = "USDT") -> float:
        """Free (available) spot balance of one asset."""
        for b in self.account().get("balances", []):
            if b.get("asset") == asset:
                return float(b.get("free", 0) or 0)
        return 0.0

    # -- transfers ------------------------------------------------------

    def transfer(
        self, from_account: str, to_account: str, asset: str, amount: float
    ) -> Any:
        """Move funds between internal wallets. ``POST /api/v3/capital/transfer``.

        Args:
            from_account / to_account: e.g. ``"SPOT"`` or ``"FUTURES"``
                (constants :data:`SPOT`, :data:`FUTURES`).
            asset: currency, e.g. ``"USDT"``.
            amount: quantity to move.

        Returns the raw response (``{"tranId": ...}`` on success). Requires the
        API key's Transfer/Wallet permission (else error 700007).
        """
        return self._request(
            "POST",
            "/api/v3/capital/transfer",
            {
                "fromAccountType": from_account,
                "toAccountType": to_account,
                "asset": asset,
                "amount": amount,
            },
        )

    def transfer_to_futures(self, amount: float, asset: str = "USDT") -> Any:
        """Convenience: SPOT -> FUTURES."""
        return self.transfer(SPOT, FUTURES, asset, amount)

    def transfer_to_spot(self, amount: float, asset: str = "USDT") -> Any:
        """Convenience: FUTURES -> SPOT."""
        return self.transfer(FUTURES, SPOT, asset, amount)

    def transfer_to_funding(
        self, amount: float, asset: str = "USDT", *, from_account: str = SPOT
    ) -> Any:
        """Convenience: <from_account> -> FUND (funding / fiat wallet)."""
        return self.transfer(from_account, FUND, asset, amount)

    def transfer_from_funding(
        self, amount: float, asset: str = "USDT", *, to_account: str = SPOT
    ) -> Any:
        """Convenience: FUND (funding / fiat wallet) -> <to_account>."""
        return self.transfer(FUND, to_account, asset, amount)

    def transfer_history(
        self, from_account: str = SPOT, to_account: str = FUTURES
    ) -> Any:
        """Transfer history between two wallets. ``GET /api/v3/capital/transfer``."""
        resp = self._request(
            "GET",
            "/api/v3/capital/transfer",
            {"fromAccountType": from_account, "toAccountType": to_account},
        )
        return resp.get("rows", resp) if isinstance(resp, dict) else resp

    # -- deposit --------------------------------------------------------

    def deposit_address(self, coin: str, network: str) -> Any:
        """Deposit address for a coin/network. ``POST /api/v3/capital/deposit/address``."""
        return self._request(
            "POST", "/api/v3/capital/deposit/address", {"coin": coin, "network": network}
        )
