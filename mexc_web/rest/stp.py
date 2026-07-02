"""Self-trade-prevention (STP) group / market-maker blacklist endpoints."""

from __future__ import annotations

from typing import Any

from .base import Namespace, clean

__all__ = ["StpAPI"]


class StpAPI(Namespace):
    """Self-trade-prevention groups (web-token auth)."""

    def list(self, **query: Any) -> Any:
        """STP groups and members. ``GET /private/market_maker/self_trade/blacklist``."""
        return self._t.request(
            "GET", "/private/market_maker/self_trade/blacklist", params=clean(query)
        )

    def current(self, **query: Any) -> Any:
        """Current user's STP group. ``GET .../self_trade/blacklist/search``."""
        return self._t.request(
            "GET", "/private/market_maker/self_trade/blacklist/search", params=clean(query)
        )

    def create(self, **body: Any) -> Any:
        """Create an STP group. ``POST .../self_trade/blacklist/create``."""
        return self._t.request(
            "POST", "/private/market_maker/self_trade/blacklist/create", params=body
        )

    def update(self, **body: Any) -> Any:
        """Update an STP group. ``POST .../self_trade/blacklist/update``."""
        return self._t.request(
            "POST", "/private/market_maker/self_trade/blacklist/update", params=body
        )

    def delete(self, **body: Any) -> Any:
        """Delete an STP group. ``POST .../self_trade/blacklist/delete``."""
        return self._t.request(
            "POST", "/private/market_maker/self_trade/blacklist/delete", params=body
        )
