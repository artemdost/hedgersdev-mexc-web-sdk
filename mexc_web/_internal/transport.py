"""HTTP transport + web-token signing for the MEXC futures API.

The signing scheme is the one the MEXC web UI itself uses (the ``u_id`` browser
cookie, a.k.a. the "web token"). It is an MD5-based scheme, *not* the public
OpenAPI HMAC-SHA256 scheme:

    postfix    = md5(token + ts).hexdigest()[7:]
    signature  = md5(ts + serialized_body + postfix).hexdigest()

``ts`` (millisecond timestamp) is echoed in the ``x-mxc-nonce`` header and the
signature goes in ``x-mxc-sign``; the token itself is sent verbatim in
``Authorization``.

To guarantee the bytes we *sign* are byte-for-byte the bytes we *send*, the body
is serialized once here and passed to ``requests`` as raw ``data`` — never
re-serialized by the HTTP layer.
"""

from __future__ import annotations

import hashlib
import json
import os
from time import time
from typing import Any

import requests

from .errors import MexcAPIError, MexcAuthError, MexcHTTPError

__all__ = ["Transport"]

_DEFAULT_BASE_URL = "https://futures.mexc.com/api/v1"


class Transport:
    """Signs and executes HTTP requests against the MEXC futures web API."""

    def __init__(
        self,
        token: str | None = None,
        *,
        base_url: str = _DEFAULT_BASE_URL,
        timeout: float = 10.0,
        session: requests.Session | None = None,
        user_agent: str = "mexc-web/0.1 (+https://github.com/artemdost/mexc-web-sdk)",
    ) -> None:
        self._token = token
        self._base_url = base_url.rstrip("/")
        self._timeout = timeout
        self._ua = user_agent
        self._session = session or requests.Session()

    # -- public surface -------------------------------------------------

    @property
    def token(self) -> str | None:
        return self._token

    def set_token(self, token: str) -> None:
        """Swap the web token in place (e.g. after refreshing it from cookies)."""
        self._token = token

    def close(self) -> None:
        self._session.close()

    def request(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, Any] | list[Any] | None = None,
        auth: bool = True,
    ) -> Any:
        """Execute a request and return the decoded JSON.

        Args:
            method: HTTP verb.
            path: Endpoint path relative to the base URL (leading ``/``).
            params: For GET — query parameters (dict). For POST — the JSON body
                (dict or list).
            auth: Whether to sign the request with the web token. Public market
                endpoints pass ``auth=False``.

        Raises:
            MexcAuthError: ``auth=True`` but no token was configured.
            MexcHTTPError: non-2xx HTTP status.
            MexcAPIError: HTTP 200 but MEXC returned ``success: false``.
        """
        method = method.upper()
        url, query, body_obj = self._prepare(method, path, params)

        headers = self._base_headers()
        data: bytes | None = None

        if auth:
            if not self._token:
                raise MexcAuthError(
                    f"{method} {path} requires a web token; construct the client with one"
                )
            serialized, sign, ts = self._sign(body_obj, self._token)
            headers.update(
                {
                    "x-mxc-sign": sign,
                    "x-mxc-nonce": ts,
                    "Authorization": self._token,
                }
            )
            if method != "GET" and body_obj is not None:
                data = serialized.encode()
        elif method != "GET" and body_obj is not None:
            data = json.dumps(body_obj).encode()

        resp = self._session.request(
            method=method,
            url=url + query,
            headers=headers,
            data=data,
            timeout=self._timeout,
        )
        if not resp.ok:
            raise MexcHTTPError(resp.status_code, resp.text)

        try:
            payload = resp.json()
        except ValueError:
            raise MexcHTTPError(resp.status_code, resp.text)

        # MEXC envelope: {"success": bool, "code": int, "data": ..., "message": ...}
        if isinstance(payload, dict) and payload.get("success") is False:
            raise MexcAPIError(
                payload.get("code"),
                str(payload.get("message") or payload.get("msg") or "request failed"),
                payload,
            )
        return payload

    # -- internals ------------------------------------------------------

    def _prepare(
        self,
        method: str,
        path: str,
        params: dict[str, Any] | list[Any] | None,
    ) -> tuple[str, str, dict[str, Any] | list[Any] | None]:
        """Return (url, query_string, body_object)."""
        url = f"{self._base_url}{path}"
        query = ""
        body: dict[str, Any] | list[Any] | None = None

        if method == "GET":
            if isinstance(params, dict):
                filtered = {k: v for k, v in params.items() if v is not None}
                if filtered:
                    query = "?" + "&".join(f"{k}={v}" for k, v in filtered.items())
        else:
            body = params
        return url, query, body

    def _base_headers(self) -> dict[str, str]:
        """Browser-emulating headers common to every request."""
        return {
            "User-Agent": self._ua,
            "Accept": "*/*",
            "Accept-Language": "en-US,en;q=0.5",
            "Content-Type": "application/json",
            "Language": "English",
            "Pragma": "akamai-x-cache-on",
            "Origin": "https://futures.mexc.com",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-origin",
        }

    @staticmethod
    def _sign(
        body: dict[str, Any] | list[Any] | None,
        token: str,
    ) -> tuple[str, str, str]:
        """Return (serialized_body, signature, timestamp).

        Mirrors the MEXC web client: dict bodies get ``chash``/``ts`` injected
        and are signed as sent; list bodies (e.g. bulk cancel) are signed and
        sent verbatim.
        """
        ts = str(int(time() * 1000))
        randomness = os.urandom(16).hex()

        if isinstance(body, list):
            send_obj: dict[str, Any] | list[Any] = body
        else:
            send_obj = dict(body) if body else {}
            send_obj.update({"chash": randomness, "ts": ts})

        serialized = json.dumps(send_obj)
        signature = Transport._generate_signature(token, serialized, ts)
        return serialized, signature, ts

    @staticmethod
    def _generate_signature(token: str, serialized: str, ts: str) -> str:
        md5_hash = hashlib.md5(f"{token}{ts}".encode()).hexdigest()
        postfix = md5_hash[7:]
        return hashlib.md5(f"{ts}{serialized}{postfix}".encode()).hexdigest()
