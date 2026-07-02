"""Position management endpoints."""

from __future__ import annotations

from typing import Any

from .base import Namespace, clean

__all__ = ["PositionsAPI"]


class PositionsAPI(Namespace):
    """Positions, leverage, margin and position-mode (web-token auth)."""

    def open(self, symbol: str | None = None) -> Any:
        """Open positions. ``GET /private/position/open_positions``."""
        return self._t.request(
            "GET", "/private/position/open_positions", params=clean({"symbol": symbol})
        )

    def history(
        self,
        symbol: str | None = None,
        type: int | None = None,
        page_num: int | None = None,
        page_size: int | None = None,
    ) -> Any:
        """Historical positions. ``GET /private/position/list/history_positions``."""
        return self._t.request(
            "GET",
            "/private/position/list/history_positions",
            params=clean(
                {"symbol": symbol, "type": type, "page_num": page_num, "page_size": page_size}
            ),
        )

    def leverage(self, symbol: str | None = None, position_id: int | None = None) -> Any:
        """Current leverage / leverage multipliers. ``GET /private/position/leverage``."""
        return self._t.request(
            "GET",
            "/private/position/leverage",
            params=clean({"symbol": symbol, "positionId": position_id}),
        )

    def get_mode(self) -> Any:
        """Position mode (1 dual-side, 2 one-way). ``GET /private/position/position_mode``."""
        return self._t.request("GET", "/private/position/position_mode")

    def set_mode(self, position_mode: int) -> Any:
        """Set position mode. ``POST /private/position/change_position_mode``.

        ``position_mode``: 1 dual-side (hedge), 2 one-way.
        """
        return self._t.request(
            "POST", "/private/position/change_position_mode", params={"positionMode": position_mode}
        )

    def set_leverage(
        self,
        leverage: int,
        *,
        position_id: int | None = None,
        open_type: int | None = None,
        symbol: str | None = None,
        position_type: int | None = None,
        **extra: Any,
    ) -> Any:
        """Change leverage. ``POST /private/position/change_leverage``.

        Provide ``position_id`` for an existing position, or
        ``symbol`` + ``open_type`` (1 isolated, 2 cross) + ``position_type``
        (1 long, 2 short) to set it before opening.
        """
        body = clean(
            {
                "leverage": leverage,
                "positionId": position_id,
                "openType": open_type,
                "symbol": symbol,
                "positionType": position_type,
                **extra,
            }
        )
        return self._t.request("POST", "/private/position/change_leverage", params=body)

    def change_margin(
        self, position_id: int, amount: float, type: str, **extra: Any
    ) -> Any:
        """Add/reduce isolated margin. ``POST /private/position/change_margin``.

        ``type``: "ADD" or "SUB".
        """
        body = clean({"positionId": position_id, "amount": amount, "type": type, **extra})
        return self._t.request("POST", "/private/position/change_margin", params=body)

    def set_auto_add_margin(self, position_id: int, auto_add_im: bool, **extra: Any) -> Any:
        """Enable/disable auto add margin. ``POST /private/position/change_auto_add_im``."""
        body = clean({"positionId": position_id, "autoAddIm": auto_add_im, **extra})
        return self._t.request("POST", "/private/position/change_auto_add_im", params=body)

    def close_all(self, **body: Any) -> Any:
        """Market-close every position. ``POST /private/position/close_all``."""
        return self._t.request("POST", "/private/position/close_all", params=body or None)

    def reverse(self, **body: Any) -> Any:
        """Reverse a position (close and open the opposite side).

        ``POST /private/position/reverse``.
        """
        return self._t.request("POST", "/private/position/reverse", params=body)

    def funding_records(
        self,
        symbol: str | None = None,
        position_id: int | None = None,
        page_num: int | None = None,
        page_size: int | None = None,
    ) -> Any:
        """Funding-fee records. ``GET /private/position/funding_records``."""
        return self._t.request(
            "GET",
            "/private/position/funding_records",
            params=clean(
                {
                    "symbol": symbol,
                    "position_id": position_id,
                    "page_num": page_num,
                    "page_size": page_size,
                }
            ),
        )
