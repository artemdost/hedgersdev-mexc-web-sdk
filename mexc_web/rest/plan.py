"""Plan (conditional / trigger) order endpoints."""

from __future__ import annotations

from typing import Any

from .base import Namespace, clean

__all__ = ["PlanOrdersAPI"]


class PlanOrdersAPI(Namespace):
    """Conditional "plan" orders that trigger at a target price (web-token auth)."""

    def place(self, **body: Any) -> Any:
        """Place a plan order. ``POST /private/planorder/place/v2``."""
        return self._t.request("POST", "/private/planorder/place/v2", params=body)

    def cancel(self, items: list[dict[str, Any]]) -> Any:
        """Cancel plan orders. ``POST /private/planorder/cancel``."""
        return self._t.request("POST", "/private/planorder/cancel", params=items)

    def cancel_all(self, **body: Any) -> Any:
        """Cancel all plan orders. ``POST /private/planorder/cancel_all``."""
        return self._t.request("POST", "/private/planorder/cancel_all", params=body or None)

    def change_price(self, **body: Any) -> Any:
        """Modify a plan order's price. ``POST /private/planorder/change_price``."""
        return self._t.request("POST", "/private/planorder/change_price", params=body)

    def change_stop_order(self, **body: Any) -> Any:
        """Modify TP/SL attached to a plan order.

        ``POST /private/planorder/change_stop_order``.
        """
        return self._t.request("POST", "/private/planorder/change_stop_order", params=body)

    def list(self, **query: Any) -> Any:
        """List plan orders. ``GET /private/planorder/list/orders``."""
        return self._t.request("GET", "/private/planorder/list/orders", params=clean(query))
