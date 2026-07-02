"""Offline tests: signing, headers, URL/body construction, auth guard.

No network, the requests.Session is stubbed.
"""

import hashlib
import json

import pytest

from mexc_web import MexcAuthError, MexcClient
from mexc_web._internal.transport import Transport

TOKEN = "WEB_test_token_0123456789abcdef"


class FakeResp:
    def __init__(self, payload, status=200):
        self._payload = payload
        self.status_code = status
        self.ok = 200 <= status < 300
        self.text = json.dumps(payload)

    def json(self):
        return self._payload


class FakeSession:
    """Captures the last request and returns a canned success envelope."""

    def __init__(self):
        self.calls = []

    def request(self, **kwargs):
        self.calls.append(kwargs)
        return FakeResp({"success": True, "code": 0, "data": "ok"})

    def close(self):
        pass


def make_client():
    sess = FakeSession()
    return MexcClient(TOKEN, session=sess), sess


def test_signature_matches_reference_formula():
    ser, sign, ts = Transport._sign({"symbol": "BTC_USDT"}, TOKEN)
    postfix = hashlib.md5(f"{TOKEN}{ts}".encode()).hexdigest()[7:]
    expect = hashlib.md5(f"{ts}{ser}{postfix}".encode()).hexdigest()
    assert sign == expect
    body = json.loads(ser)
    assert body["symbol"] == "BTC_USDT"
    assert body["ts"] == ts and "chash" in body


def test_list_body_signed_and_sent_verbatim():
    ser, _sign, _ts = Transport._sign([1, 2, 3], TOKEN)
    assert ser == json.dumps([1, 2, 3])


def test_get_builds_query_and_auth_headers():
    c, sess = make_client()
    c.positions.open("BTC_USDT")
    call = sess.calls[-1]
    assert call["method"] == "GET"
    assert call["url"].endswith("/private/position/open_positions?symbol=BTC_USDT")
    for h in ("x-mxc-sign", "x-mxc-nonce", "Authorization"):
        assert h in call["headers"]
    assert call["headers"]["Authorization"] == TOKEN
    assert call["data"] is None  # GET carries no body


def test_post_sends_signed_bytes():
    c, sess = make_client()
    c.orders.cancel_all("ETH_USDT")
    call = sess.calls[-1]
    assert call["method"] == "POST"
    assert call["url"].endswith("/private/order/cancel_all")
    # bytes sent must equal bytes signed
    sent = call["data"].decode()
    ts = call["headers"]["x-mxc-nonce"]
    postfix = hashlib.md5(f"{TOKEN}{ts}".encode()).hexdigest()[7:]
    expect = hashlib.md5(f"{ts}{sent}{postfix}".encode()).hexdigest()
    assert call["headers"]["x-mxc-sign"] == expect
    assert json.loads(sent)["symbol"] == "ETH_USDT"


def test_public_endpoint_needs_no_token():
    sess = FakeSession()
    c = MexcClient(session=sess)  # no token
    c.market.ticker("BTC_USDT")
    call = sess.calls[-1]
    assert "Authorization" not in call["headers"]


def test_private_without_token_raises():
    c = MexcClient(session=FakeSession())
    with pytest.raises(MexcAuthError):
        c.account.assets()
