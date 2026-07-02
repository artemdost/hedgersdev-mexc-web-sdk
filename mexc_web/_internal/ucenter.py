"""Access to the MEXC ucenter API (account identity: email, uid, ...).

ucenter lives on ``www.mexc.com``, a different host from the futures API and a
different auth scheme: the web token goes in the ``ucenter-token`` header, and
there is **no** MD5 signature.

``www.mexc.com`` sits behind Akamai, which sometimes rejects non-Chrome TLS
fingerprints with HTTP 403 even when the HTTP headers are perfect. We send the
full Chrome client-hint header set with ``requests`` first; if that returns 403
we transparently retry via a ``curl --compressed`` subprocess (curl ships a
standard JA3 that Akamai accepts). If neither is available/allowed the 403 is
surfaced as :class:`MexcHTTPError`.
"""

from __future__ import annotations

import json
import shutil
import subprocess
from typing import Any

import requests

from .errors import MexcAPIError, MexcAuthError, MexcHTTPError

__all__ = ["ucenter_request", "UCENTER_BASE"]

UCENTER_BASE = "https://www.mexc.com"

_CHROME_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.9",
    "sec-ch-ua": '"Chromium";v="124", "Google Chrome";v="124", "Not-A.Brand";v="99"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"Windows"',
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "same-origin",
    "Origin": "https://www.mexc.com",
    "Referer": "https://www.mexc.com/",
}


def _headers(token: str, *, via_h5: bool, post: bool) -> dict[str, str]:
    h = dict(_CHROME_HEADERS)
    h["ucenter-token"] = token
    if via_h5:
        h["ucenter-via"] = "H5"
    if post:
        h["Content-Type"] = "application/json"
    return h


def _parse(status: int, text: str) -> Any:
    if not (200 <= status < 300):
        raise MexcHTTPError(status, text)
    try:
        payload = json.loads(text)
    except ValueError:
        raise MexcHTTPError(status, text)
    if isinstance(payload, dict) and payload.get("success") is False:
        raise MexcAPIError(
            payload.get("code"),
            str(payload.get("message") or payload.get("msg") or "ucenter request failed"),
            payload,
        )
    return payload


def _curl_fallback(method: str, url: str, headers: dict[str, str], body: str | None) -> Any:
    curl = shutil.which("curl")
    if not curl:
        raise MexcHTTPError(403, "Akamai blocked the request and curl is unavailable for fallback")
    cmd = [curl, "-s", "--compressed", "--max-time", "12", "-w", "\n%{http_code}"]
    if method != "GET":
        cmd += ["-X", method]
    for k, v in headers.items():
        cmd += ["-H", f"{k}: {v}"]
    if body is not None:
        cmd += ["--data", body]
    cmd.append(url)
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
    out = proc.stdout or ""
    nl = out.rfind("\n")
    text, code = (out[:nl], out[nl + 1 :]) if nl >= 0 else (out, "0")
    try:
        status = int(code.strip() or "0")
    except ValueError:
        status = 0
    return _parse(status, text)


def ucenter_request(
    method: str,
    path: str,
    token: str | None,
    *,
    session: requests.Session | None = None,
    via_h5: bool = False,
    body: dict[str, Any] | None = None,
    timeout: float = 10.0,
) -> Any:
    """Call a ucenter endpoint and return decoded JSON.

    Args:
        method: "GET" or "POST".
        path: e.g. ``/ucenter/api/origin_info``.
        token: the web (``u_id``) token; required.
        via_h5: send the ``ucenter-via: H5`` header (needed by ``user_info``).
        body: JSON body for POST (defaults to ``{}``).
    """
    if not token:
        raise MexcAuthError(f"{method} {path} requires a web token")

    method = method.upper()
    url = f"{UCENTER_BASE}{path}"
    is_post = method != "GET"
    headers = _headers(token, via_h5=via_h5, post=is_post)
    data = json.dumps(body or {}) if is_post else None

    sess = session or requests
    resp = sess.request(method, url, headers=headers, data=data, timeout=timeout)

    # Akamai edge block -> retry with curl (standard JA3).
    if resp.status_code == 403:
        return _curl_fallback(method, url, headers, data)

    return _parse(resp.status_code, resp.text)
