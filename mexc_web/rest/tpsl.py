"""Take-profit / stop-loss (stop order) endpoints."""

from __future__ import annotations

from typing import Any

from .base import Namespace, clean

__all__ = ["TpslAPI"]


class TpslAPI(Namespace):
    """Take-profit / stop-loss orders (web-token auth)."""

    def place(self, **body: Any) -> Any:
        """Place a TP/SL order against a position. ``POST /private/stoporder/place``."""
        return self._t.request("POST", "/private/stoporder/place", params=body)

    def cancel(self, items: list[dict[str, Any]]) -> Any:
        """Cancel TP/SL orders. ``POST /private/stoporder/cancel``."""
        return self._t.request("POST", "/private/stoporder/cancel", params=items)

    def cancel_all(self, **body: Any) -> Any:
        """Cancel all TP/SL planned orders. ``POST /private/stoporder/cancel_all``."""
        return self._t.request("POST", "/private/stoporder/cancel_all", params=body or None)

    def change_price(self, **body: Any) -> Any:
        """Modify TP/SL prices on a limit order. ``POST /private/stoporder/change_price``."""
        return self._t.request("POST", "/private/stoporder/change_price", params=body)

    def change_plan_price(self, **body: Any) -> Any:
        """Modify TP/SL prices on a TP/SL planned order.

        ``POST /private/stoporder/change_plan_price``.
        """
        return self._t.request("POST", "/private/stoporder/change_plan_price", params=body)

    def list(self, **query: Any) -> Any:
        """List TP/SL orders. ``GET /private/stoporder/list/orders``."""
        return self._t.request("GET", "/private/stoporder/list/orders", params=clean(query))

    def open_orders(self, **query: Any) -> Any:
        """Current TP/SL orders. ``GET /private/stoporder/open_orders``."""
        return self._t.request("GET", "/private/stoporder/open_orders", params=clean(query))
