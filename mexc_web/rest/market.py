"""Public market-data endpoints (no authentication required)."""

from __future__ import annotations

from typing import Any

from .base import Namespace, clean

__all__ = ["MarketAPI"]


class MarketAPI(Namespace):
    """Public contract / market-data endpoints.

    These work without a token; if a token is present it is simply not sent.
    """

    def ping(self) -> Any:
        """Server time. ``GET /contract/ping``."""
        return self._t.request("GET", "/contract/ping", auth=False)

    def server_time(self) -> Any:
        """Alias for :meth:`ping`."""
        return self.ping()

    def contract_detail(self, symbol: str | None = None) -> Any:
        """Contract specifications. ``GET /contract/detail``."""
        return self._t.request(
            "GET", "/contract/detail", params=clean({"symbol": symbol}), auth=False
        )

    def support_currencies(self) -> Any:
        """Currencies transferable to/from the futures wallet.

        ``GET /contract/support_currencies``.
        """
        return self._t.request("GET", "/contract/support_currencies", auth=False)

    def depth(self, symbol: str, limit: int | None = None) -> Any:
        """Order-book depth. ``GET /contract/depth/{symbol}``."""
        return self._t.request(
            "GET", f"/contract/depth/{symbol}", params=clean({"limit": limit}), auth=False
        )

    def depth_snapshots(self, symbol: str, limit: int) -> Any:
        """Last ``N`` depth snapshots. ``GET /contract/depth_commits/{symbol}/{limit}``."""
        return self._t.request("GET", f"/contract/depth_commits/{symbol}/{limit}", auth=False)

    def index_price(self, symbol: str) -> Any:
        """Index price. ``GET /contract/index_price/{symbol}``."""
        return self._t.request("GET", f"/contract/index_price/{symbol}", auth=False)

    def fair_price(self, symbol: str) -> Any:
        """Fair (mark) price. ``GET /contract/fair_price/{symbol}``."""
        return self._t.request("GET", f"/contract/fair_price/{symbol}", auth=False)

    def funding_rate(self, symbol: str) -> Any:
        """Current funding rate. ``GET /contract/funding_rate/{symbol}``."""
        return self._t.request("GET", f"/contract/funding_rate/{symbol}", auth=False)

    def funding_rate_history(
        self, symbol: str, page_num: int | None = None, page_size: int | None = None
    ) -> Any:
        """Funding-rate history. ``GET /contract/funding_rate/history``."""
        return self._t.request(
            "GET",
            "/contract/funding_rate/history",
            params=clean({"symbol": symbol, "page_num": page_num, "page_size": page_size}),
            auth=False,
        )

    def klines(
        self,
        symbol: str,
        interval: str = "Min1",
        start: int | None = None,
        end: int | None = None,
    ) -> Any:
        """Candlesticks. ``GET /contract/kline/{symbol}``.

        ``interval`` is one of Min1, Min5, Min15, Min30, Min60, Hour4, Hour8,
        Day1, Week1, Month1.
        """
        params = clean({"interval": interval, "start": start, "end": end})
        return self._t.request("GET", f"/contract/kline/{symbol}", params=params, auth=False)

    def index_price_klines(
        self, symbol: str, interval: str = "Min1", start: int | None = None, end: int | None = None
    ) -> Any:
        """Index-price candles. ``GET /contract/kline/index_price/{symbol}``."""
        params = clean({"interval": interval, "start": start, "end": end})
        return self._t.request(
            "GET", f"/contract/kline/index_price/{symbol}", params=params, auth=False
        )

    def fair_price_klines(
        self, symbol: str, interval: str = "Min1", start: int | None = None, end: int | None = None
    ) -> Any:
        """Fair-price candles. ``GET /contract/kline/fair_price/{symbol}``."""
        params = clean({"interval": interval, "start": start, "end": end})
        return self._t.request(
            "GET", f"/contract/kline/fair_price/{symbol}", params=params, auth=False
        )

    def deals(self, symbol: str, limit: int | None = None) -> Any:
        """Recent trades. ``GET /contract/deals/{symbol}``."""
        return self._t.request(
            "GET", f"/contract/deals/{symbol}", params=clean({"limit": limit}), auth=False
        )

    def ticker(self, symbol: str | None = None) -> Any:
        """Ticker(s). ``GET /contract/ticker``."""
        return self._t.request(
            "GET", "/contract/ticker", params=clean({"symbol": symbol}), auth=False
        )

    def insurance_fund(self, symbol: str) -> Any:
        """Insurance-fund balance. ``GET /contract/risk_reverse/{symbol}``."""
        return self._t.request("GET", f"/contract/risk_reverse/{symbol}", auth=False)

    def insurance_fund_history(
        self, symbol: str, page_num: int | None = None, page_size: int | None = None
    ) -> Any:
        """Insurance-fund history. ``GET /contract/risk_reverse/history``."""
        return self._t.request(
            "GET",
            "/contract/risk_reverse/history",
            params=clean({"symbol": symbol, "page_num": page_num, "page_size": page_size}),
            auth=False,
        )
