"""Offline tests for the spot (API-key) client: signing + transfer params."""

import hashlib
import hmac
import json
from urllib.parse import parse_qsl

from mexc_web import MexcSpotClient

KEY = "test_key"
SECRET = "test_secret"


class FakeResp:
    def __init__(self, payload, status=200):
        self.status_code = status
        self.ok = 200 <= status < 300
        self.text = json.dumps(payload)

    def json(self):
        return json.loads(self.text)


class FakeSession:
    def __init__(self, payload):
        self._payload = payload
        self.calls = []

    def request(self, method, url, **kw):
        self.calls.append((method, url, kw))
        return FakeResp(self._payload)

    def close(self):
        pass


def _verify_signature(url):
    """The signature in the URL must be HMAC-SHA256 of the query minus signature."""
    base, query = url.split("?", 1)
    pairs = query.split("&signature=")
    signed_part, sig = pairs[0], pairs[1]
    expect = hmac.new(SECRET.encode(), signed_part.encode(), hashlib.sha256).hexdigest()
    return sig == expect, dict(parse_qsl(signed_part))


def test_transfer_signs_and_sends_correct_params():
    sess = FakeSession({"tranId": "123"})
    spot = MexcSpotClient(KEY, SECRET, session=sess)
    r = spot.transfer_to_futures(25, "USDT")
    assert r["tranId"] == "123"
    method, url, kw = sess.calls[-1]
    assert method == "POST"
    assert kw["headers"]["X-MEXC-APIKEY"] == KEY
    ok, params = _verify_signature(url)
    assert ok, "HMAC signature mismatch"
    assert params["fromAccountType"] == "SPOT"
    assert params["toAccountType"] == "FUTURES"
    assert params["asset"] == "USDT"
    assert params["amount"] == "25"
    assert "timestamp" in params


def test_balances_filters_zero():
    payload = {
        "balances": [
            {"asset": "USDT", "free": "51.8", "locked": "0"},
            {"asset": "BTC", "free": "0", "locked": "0"},
        ]
    }
    spot = MexcSpotClient(KEY, SECRET, session=FakeSession(payload))
    bals = spot.balances()
    assert len(bals) == 1
    assert bals[0]["asset"] == "USDT" and bals[0]["total"] == 51.8


def test_deposit_address_path():
    spot = MexcSpotClient(KEY, SECRET, session=FakeSession({"address": "T..."}))
    spot.deposit_address("USDT", "TRC20")
    _method, url, _kw = spot._session.calls[-1]
    assert "/api/v3/capital/deposit/address" in url
    ok, params = _verify_signature(url)
    assert ok
    assert params["coin"] == "USDT" and params["network"] == "TRC20"
