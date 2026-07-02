"""Account identity endpoints (ucenter on www.mexc.com): email, uid, profile."""

from __future__ import annotations

from typing import Any

from .._internal.ucenter import ucenter_request
from .base import Namespace

__all__ = ["UserAPI"]


class UserAPI(Namespace):
    """Personal account data behind the ``ucenter-token`` header.

    These endpoints live on ``www.mexc.com`` (not the futures host) and use the
    web token directly, no MD5 signature. ``www.mexc.com`` is Akamai-guarded;
    the transport falls back to a ``curl`` subprocess if a 403 is returned.
    """

    def origin_info(self) -> Any:
        """Raw account origin info. ``GET /ucenter/api/origin_info``.

        ``data`` includes ``email`` and other registration details.
        """
        return ucenter_request(
            "GET", "/ucenter/api/origin_info", self._t.token, session=self._t.session
        )

    def email(self) -> str | None:
        """Convenience: the account email, or ``None`` if unavailable."""
        resp = self.origin_info()
        data = resp.get("data") if isinstance(resp, dict) else None
        if isinstance(data, dict):
            email = (data.get("email") or "").strip()
            return email or None
        return None

    def user_info(self) -> Any:
        """Account profile. ``POST /ucenter/api/user_info``.

        ``data`` includes ``digitalId`` (numeric uid), nickname, avatar, etc.
        """
        return ucenter_request(
            "POST",
            "/ucenter/api/user_info",
            self._t.token,
            session=self._t.session,
            via_h5=True,
            body={},
        )

    def uid(self) -> str | None:
        """Convenience: the numeric account uid (``digitalId``), or ``None``."""
        resp = self.user_info()
        data = resp.get("data") if isinstance(resp, dict) else None
        if isinstance(data, dict):
            uid = str(data.get("digitalId") or "").strip()
            return uid or None
        return None
