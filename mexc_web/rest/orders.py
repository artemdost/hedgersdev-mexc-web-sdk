"""Order placement, cancellation and query endpoints."""

from __future__ import annotations

from typing import Any

from .base import Namespace, clean

__all__ = ["OrdersAPI"]

# Order side
OPEN_LONG = 1
CLOSE_SHORT = 2
OPEN_SHORT = 3
CLOSE_LONG = 4

# Order type
LIMIT = 1
POST_ONLY = 2
IOC = 3
FOK = 4
MARKET = 5

# Open type
ISOLATED = 1
CROSS = 2


class OrdersAPI(Namespace):
    """Futures orders (web-token auth)."""

    def create(
        self,
        symbol: str,
        side: int,
        vol: float,
        type: int = LIMIT,
        *,
        price: float | None = None,
        open_type: int = ISOLATED,
        leverage: int | None = None,
        position_id: int | None = None,
        external_oid: str | None = None,
        position_mode: int | None = None,
        reduce_only: bool | None = None,
        stop_loss_price: float | None = None,
        take_profit_price: float | None = None,
        stp_mode: int | None = None,
        **extra: Any,
    ) -> Any:
        """Place an order. ``POST /private/order/create``.

        Args:
            symbol: e.g. ``"BTC_USDT"``.
            side: 1 open-long, 2 close-short, 3 open-short, 4 close-long
                (see module constants ``OPEN_LONG`` etc.).
            vol: quantity in contracts.
            type: 1 limit, 2 post-only, 3 IOC, 4 FOK, 5 market
                (constants ``LIMIT``/``MARKET``/...).
            price: required for non-market orders.
            open_type: 1 isolated, 2 cross.
            leverage: required when opening a position.
            **extra: any other field accepted by MEXC (e.g. ``bboTypeNum``,
                ``marketCeiling``, ``priceProtect``, ``lossTrend`` ...).
        """
        body = clean(
            {
                "symbol": symbol,
                "side": side,
                "vol": vol,
                "type": type,
                "price": price,
                "openType": open_type,
                "leverage": leverage,
                "positionId": position_id,
                "externalOid": external_oid,
                "positionMode": position_mode,
                "reduceOnly": reduce_only,
                "stopLossPrice": stop_loss_price,
                "takeProfitPrice": take_profit_price,
                "stpMode": stp_mode,
                **extra,
            }
        )
        return self._t.request("POST", "/private/order/create", params=body)

    def create_raw(self, payload: dict[str, Any]) -> Any:
        """Place an order from a raw payload dict (escape hatch)."""
        return self._t.request("POST", "/private/order/create", params=payload)

    def batch_create(self, orders: list[dict[str, Any]]) -> Any:
        """Place up to 50 orders at once. ``POST /private/order/submit_batch``."""
        return self._t.request("POST", "/private/order/submit_batch", params=orders)

    def cancel(self, order_ids: list[int | str]) -> Any:
        """Cancel orders by id (max 50). ``POST /private/order/cancel``."""
        return self._t.request("POST", "/private/order/cancel", params=list(order_ids))

    def cancel_all(self, symbol: str | None = None) -> Any:
        """Cancel all orders (optionally for one symbol).

        ``POST /private/order/cancel_all``.
        """
        return self._t.request(
            "POST", "/private/order/cancel_all", params=clean({"symbol": symbol})
        )

    def cancel_by_external(self, symbol: str, external_oid: str) -> Any:
        """Cancel by external id. ``POST /private/order/cancel_with_external``."""
        return self._t.request(
            "POST",
            "/private/order/cancel_with_external",
            params={"symbol": symbol, "externalOid": external_oid},
        )

    def batch_cancel_by_external(self, items: list[dict[str, Any]]) -> Any:
        """Batch cancel by external id. ``POST /private/order/batch_cancel_with_external``."""
        return self._t.request("POST", "/private/order/batch_cancel_with_external", params=items)

    def change_limit_order(self, order_id: int | str, price: float, vol: float, **extra: Any) -> Any:
        """Modify a limit order's price/quantity. ``POST /private/order/change_limit_order``.

        Returns a new ``orderId``; the original order is dead on success. The
        original must not have had ``stpMode`` set.
        """
        body = clean({"orderId": order_id, "price": price, "vol": vol, **extra})
        return self._t.request("POST", "/private/order/change_limit_order", params=body)

    def chase_limit_order(self, **body: Any) -> Any:
        """Chase (re-peg) a limit order. ``POST /private/order/chase_limit_order``."""
        return self._t.request("POST", "/private/order/chase_limit_order", params=body)

    def get(self, order_id: int | str) -> Any:
        """Order by id. ``GET /private/order/get/{orderId}``."""
        return self._t.request("GET", f"/private/order/get/{order_id}")

    def get_by_external(self, symbol: str, external_oid: str) -> Any:
        """Order by external id. ``GET /private/order/external/{symbol}/{external_oid}``."""
        return self._t.request("GET", f"/private/order/external/{symbol}/{external_oid}")

    def batch_query(self, order_ids: str) -> Any:
        """Query multiple orders by id. ``GET /private/order/batch_query``.

        ``order_ids`` is a comma-separated string of ids.
        """
        return self._t.request(
            "GET", "/private/order/batch_query", params={"order_ids": order_ids}
        )

    def batch_query_by_external(self, items: list[dict[str, Any]]) -> Any:
        """Query multiple orders by external id.

        ``POST /private/order/batch_query_with_external``.
        """
        return self._t.request("POST", "/private/order/batch_query_with_external", params=items)

    def open_orders(self, symbol: str | None = None, **query: Any) -> Any:
        """Current open orders. ``GET /private/order/list/open_orders``.

        A ``symbol`` narrows to one contract via the path variant.
        """
        path = "/private/order/list/open_orders"
        if symbol:
            path = f"{path}/{symbol}"
        return self._t.request("GET", path, params=clean(query))

    def history(self, **query: Any) -> Any:
        """All historical orders. ``GET /private/order/list/history_orders``."""
        return self._t.request(
            "GET", "/private/order/list/history_orders", params=clean(query)
        )

    def closed(self, **query: Any) -> Any:
        """Historical (closed) orders. ``GET /private/order/list/close_orders``."""
        return self._t.request(
            "GET", "/private/order/list/close_orders", params=clean(query)
        )

    def deals(self, order_id: int | str, **query: Any) -> Any:
        """Fills for one order. ``GET /private/order/deal_details/{orderId}``."""
        return self._t.request(
            "GET", f"/private/order/deal_details/{order_id}", params=clean(query)
        )

    def all_deals(self, **query: Any) -> Any:
        """All historical fills. ``GET /private/order/list/order_deals/v3``."""
        return self._t.request(
            "GET", "/private/order/list/order_deals/v3", params=clean(query)
        )

    def fee_details(self, **query: Any) -> Any:
        """Fee-deduction details. ``GET /private/order/fee_details``."""
        return self._t.request("GET", "/private/order/fee_details", params=clean(query))

    def in_flight_count(self, **body: Any) -> Any:
        """In-flight open-order counts. ``POST /private/order/open_order_total_count``."""
        return self._t.request(
            "POST", "/private/order/open_order_total_count", params=body or None
        )
