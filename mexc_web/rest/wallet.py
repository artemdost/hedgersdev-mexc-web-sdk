"""Wallet overview + internal transfers via the web token (asset platform).

Unlike :class:`~mexc_web.rest.spot.MexcSpotClient` (which needs an API key), this
uses the **web token**, the same credential as the rest of ``MexcClient`` -
because MEXC's asset platform authenticates it as a cookie. This is what powers
the "Transfer" button in the web UI.

Wallet identifiers (the ``from``/``to`` enum used by transfers):

===========  ============================================
constant     wallet
===========  ============================================
``MAIN``     Spot account
``SWAP``     Futures (perpetual) account
``OTC``      Funding account (fiat / card purchases land here)
``STOCK``    Stock account (must be opened first)
===========  ============================================
"""

from __future__ import annotations

from typing import Any

from .._internal.asset import asset_request
from .base import Namespace

__all__ = ["WalletAPI", "MAIN", "SWAP", "OTC", "STOCK"]

# Transfer wallet identifiers (verified live against the asset platform).
MAIN = "MAIN"     # spot
SWAP = "SWAP"     # futures
OTC = "OTC"       # funding / fiat
STOCK = "STOCK"   # stock account

_OVERVIEW = "/api/platform/asset/api/asset/overview/convert/v2"
_TRANSFER = "/api/platform/asset/api/asset/transfer"


class WalletAPI(Namespace):
    """Cross-wallet balances and transfers using the web token."""

    def overview(self) -> Any:
        """Balances across every wallet. ``GET`` asset overview.

        Returns ``{"data": [{currency, total, spot, otc, contract, ...}, ...]}``
        where ``spot``/``contract``/``otc`` are the spot/futures/funding balances.
        """
        return asset_request("GET", _OVERVIEW, self._t.token, session=self._t.session)

    def balances(self) -> dict[str, dict[str, float]]:
        """Convenience: ``{currency: {wallet: amount}}`` for non-zero holdings."""
        resp = self.overview()
        rows = resp.get("data") if isinstance(resp, dict) else None
        out: dict[str, dict[str, float]] = {}
        for row in rows or []:
            cur = row.get("currency")
            wallets = {
                w: float(row[w])
                for w in ("spot", "contract", "otc", "strategy", "alpha", "financial")
                if row.get(w) not in (None, "0", "", "0.0") and float(row.get(w) or 0)
            }
            if cur and wallets:
                out[cur] = wallets
        return out

    def transfer(self, currency: str, from_wallet: str, to_wallet: str, amount: float) -> Any:
        """Move funds between wallets. ``POST`` asset transfer.

        Args:
            currency: e.g. ``"USDT"``.
            from_wallet / to_wallet: one of :data:`MAIN`, :data:`SWAP`,
                :data:`OTC`, :data:`STOCK`.
            amount: quantity to move.

        Returns ``{"code": 0, "msg": "success"}`` on success.
        """
        return asset_request(
            "POST",
            _TRANSFER,
            self._t.token,
            session=self._t.session,
            body={
                "currency": currency,
                "from": from_wallet,
                "to": to_wallet,
                "amount": str(amount),
            },
        )

    # -- convenience directions ----------------------------------------

    def spot_to_futures(self, amount: float, currency: str = "USDT") -> Any:
        return self.transfer(currency, MAIN, SWAP, amount)

    def futures_to_spot(self, amount: float, currency: str = "USDT") -> Any:
        return self.transfer(currency, SWAP, MAIN, amount)

    def spot_to_funding(self, amount: float, currency: str = "USDT") -> Any:
        """Spot -> funding (OTC) wallet."""
        return self.transfer(currency, MAIN, OTC, amount)

    def funding_to_spot(self, amount: float, currency: str = "USDT") -> Any:
        """Funding (OTC) -> spot wallet."""
        return self.transfer(currency, OTC, MAIN, amount)
