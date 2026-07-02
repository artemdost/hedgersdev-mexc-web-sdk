"""Offline tests for the web-token wallet (asset platform) namespace."""

import json

import pytest

from mexc_web import MexcAuthError, MexcClient


class FakeResp:
    def __init__(self, payload, status=200):
        self.status_code = status
        self.text = json.dumps(payload)


class AssetSession:
    def __init__(self, payload):
        self._payload = payload
        self.calls = []

    def request(self, method, url, **kw):
        self.calls.append((method, url, kw))
        return FakeResp(self._payload)

    def close(self):
        pass


def test_transfer_body_and_cookie_auth():
    sess = AssetSession({"code": 0, "msg": "success"})
    c = MexcClient("TOK", session=sess)
    r = c.wallet.spot_to_funding(5, "USDT")
    assert r["code"] == 0
    method, url, kw = sess.calls[-1]
    assert method == "POST"
    assert url.endswith("/api/platform/asset/api/asset/transfer")
    assert kw["headers"]["Cookie"] == "u_id=TOK"
    body = json.loads(kw["data"])
    assert body == {"currency": "USDT", "from": "MAIN", "to": "OTC", "amount": "5"}


def test_balances_parsing():
    payload = {"data": [
        {"currency": "USDT", "spot": "1472.81", "contract": "51.81", "otc": "1", "strategy": "0"},
        {"currency": "ZERO", "spot": "0", "contract": "0", "otc": "0"},
    ]}
    c = MexcClient("TOK", session=AssetSession(payload))
    bals = c.wallet.balances()
    assert bals["USDT"] == {"spot": 1472.81, "contract": 51.81, "otc": 1.0}
    assert "ZERO" not in bals


def test_transfer_requires_token():
    c = MexcClient()  # no token
    with pytest.raises(MexcAuthError):
        c.wallet.spot_to_funding(1)
