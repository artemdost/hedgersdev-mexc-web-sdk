"""Account, balance, fee and risk-limit endpoints."""

from __future__ import annotations

from typing import Any

from .base import Namespace, clean

__all__ = ["AccountAPI"]


class AccountAPI(Namespace):
    """Private account / asset / fee endpoints (web-token auth)."""

    def assets(self) -> Any:
        """All wallet assets. ``GET /private/account/assets``."""
        return self._t.request("GET", "/private/account/assets")

    def asset(self, currency: str) -> Any:
        """Single-currency balance. ``GET /private/account/asset/{currency}``."""
        return self._t.request("GET", f"/private/account/asset/{currency}")

    def transfer_records(
        self,
        page_num: int | None = None,
        page_size: int | None = None,
        currency: str | None = None,
        state: str | None = None,
        type: str | None = None,
    ) -> Any:
        """Spot<->futures transfer history. ``GET /private/account/transfer_record``.

        Note: this only *reads* transfer history. The web token cannot execute a
        transfer or a withdrawal, those go through the spot OpenAPI (API key).
        """
        return self._t.request(
            "GET",
            "/private/account/transfer_record",
            params=clean(
                {
                    "page_num": page_num,
                    "page_size": page_size,
                    "currency": currency,
                    "state": state,
                    "type": type,
                }
            ),
        )

    def risk_limits(self, symbol: str | None = None) -> Any:
        """Risk limits. ``GET /private/account/risk_limit``."""
        return self._t.request(
            "GET", "/private/account/risk_limit", params=clean({"symbol": symbol})
        )

    def change_risk_level(self, **body: Any) -> Any:
        """Change risk level. ``POST /private/account/change_risk_level``."""
        return self._t.request("POST", "/private/account/change_risk_level", params=body)

    def fee_rate(self, symbol: str | None = None) -> Any:
        """Per-contract fee rate. ``GET /private/account/contract/fee_rate``."""
        return self._t.request(
            "GET", "/private/account/contract/fee_rate", params=clean({"symbol": symbol})
        )

    def tiered_fee_rate(self, **query: Any) -> Any:
        """Tiered fee details. ``GET /private/account/tiered_fee_rate/v2``."""
        return self._t.request(
            "GET", "/private/account/tiered_fee_rate/v2", params=clean(query)
        )

    def fee_stats_30d(self) -> Any:
        """30-day fee statistics.

        ``GET /private/account/asset_book/order_deal_fee/total``.
        """
        return self._t.request("GET", "/private/account/asset_book/order_deal_fee/total")

    def deduction_config(self) -> Any:
        """Fee-deduction configuration. ``GET /private/account/feeDeductConfigs``."""
        return self._t.request("GET", "/private/account/feeDeductConfigs")

    def fee_discount_config(self) -> Any:
        """Spot fee-discount config. ``GET /private/account/config/contractFeeDiscountConfig``."""
        return self._t.request("GET", "/private/account/config/contractFeeDiscountConfig")

    def zero_fee_pairs(self) -> Any:
        """Zero-fee trading pairs. ``GET /private/account/contract/zero_fee_rate``."""
        return self._t.request("GET", "/private/account/contract/zero_fee_rate")

    def profit_rate(self, type: str) -> Any:
        """Personal profit rate. ``GET /private/account/profit_rate/{type}``."""
        return self._t.request("GET", f"/private/account/profit_rate/{type}")
