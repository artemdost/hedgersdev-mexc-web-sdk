"""Trailing (track) order endpoints."""

from __future__ import annotations

from typing import Any

from .base import Namespace, clean

__all__ = ["TrailingAPI"]


class TrailingAPI(Namespace):
    """Trailing-stop orders (web-token auth)."""

    def place(self, **body: Any) -> Any:
        """Place a trailing order. ``POST /private/trackorder/place``."""
        return self._t.request("POST", "/private/trackorder/place", params=body)

    def cancel(self, items: list[dict[str, Any]]) -> Any:
        """Cancel trailing orders. ``POST /private/trackorder/cancel``."""
        return self._t.request("POST", "/private/trackorder/cancel", params=items)

    def change_order(self, **body: Any) -> Any:
        """Modify a trailing order. ``POST /private/trackorder/change_order``."""
        return self._t.request("POST", "/private/trackorder/change_order", params=body)

    def list(self, **query: Any) -> Any:
        """List trailing orders. ``GET /private/trackorder/list/orders``."""
        return self._t.request("GET", "/private/trackorder/list/orders", params=clean(query))
