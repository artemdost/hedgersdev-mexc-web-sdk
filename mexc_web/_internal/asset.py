"""Access to the MEXC asset platform (wallet overview + internal transfers).

This is the endpoint the browser's own Transfer modal uses. It lives on
``www.mexc.com/api/platform/asset`` and authenticates with the web token as a
**cookie** (``u_id=<token>``) — not the futures MD5 signature and not an API
key. This is how the web token can move funds between wallets even though it
cannot on the futures host.

Like ucenter, ``www.mexc.com`` is Akamai-guarded, so we send the full Chrome
client-hint header set and fall back to ``curl --compressed`` on a 403.
"""

from __future__ import annotations

import json
import shutil
import subprocess
from typing import Any

import requests

from .errors import MexcAPIError, MexcAuthError, MexcHTTPError

__all__ = ["asset_request", "ASSET_BASE"]

ASSET_BASE = "https://www.mexc.com"

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
    "Referer": "https://www.mexc.com/assets",
}


def _headers(token: str, *, post: bool) -> dict[str, str]:
    h = dict(_CHROME_HEADERS)
    h["Cookie"] = f"u_id={token}"
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
    # Asset platform envelope: {"code": 0, "msg": "success", "data": ...}.
    # code 0 (or absent, e.g. the overview) == success; anything else is an error.
    if isinstance(payload, dict):
        code = payload.get("code")
        if code not in (0, None):
            raise MexcAPIError(code, str(payload.get("msg") or "asset request failed"), payload)
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


def asset_request(
    method: str,
    path: str,
    token: str | None,
    *,
    session: requests.Session | None = None,
    body: dict[str, Any] | None = None,
    timeout: float = 10.0,
) -> Any:
    """Call an asset-platform endpoint (cookie ``u_id`` auth) and return JSON."""
    if not token:
        raise MexcAuthError(f"{method} {path} requires a web token")

    method = method.upper()
    url = f"{ASSET_BASE}{path}"
    is_post = method != "GET"
    headers = _headers(token, post=is_post)
    data = json.dumps(body or {}) if is_post else None

    sess = session or requests
    resp = sess.request(method, url, headers=headers, data=data, timeout=timeout)
    if resp.status_code == 403:
        return _curl_fallback(method, url, headers, data)
    return _parse(resp.status_code, resp.text)
