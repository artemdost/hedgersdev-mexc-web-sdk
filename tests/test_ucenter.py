"""Offline tests for the ucenter (identity) namespace."""

import json

import pytest

from mexc_web import MexcAuthError, MexcClient


class FakeResp:
    def __init__(self, payload, status=200):
        self.status_code = status
        self.text = json.dumps(payload)


class UcenterSession:
    """Fake session matching requests.Session.request(method, url, **kw)."""

    def __init__(self, payload):
        self._payload = payload
        self.calls = []

    def request(self, method, url, **kw):
        self.calls.append((method, url, kw))
        return FakeResp(self._payload)

    def close(self):
        pass


def test_email_extracted():
    sess = UcenterSession({"success": True, "code": 0, "data": {"email": "trader@example.com"}})
    c = MexcClient("TOK", session=sess)
    assert c.user.email() == "trader@example.com"
    method, url, kw = sess.calls[-1]
    assert method == "GET"
    assert url.endswith("/ucenter/api/origin_info")
    assert kw["headers"]["ucenter-token"] == "TOK"


def test_uid_extracted_and_h5_header():
    sess = UcenterSession({"success": True, "code": 0, "data": {"digitalId": 123456789}})
    c = MexcClient("TOK", session=sess)
    assert c.user.uid() == "123456789"
    method, url, kw = sess.calls[-1]
    assert method == "POST"
    assert url.endswith("/ucenter/api/user_info")
    assert kw["headers"]["ucenter-via"] == "H5"
    assert kw["data"] == "{}"


def test_ucenter_requires_token():
    c = MexcClient()  # no token
    with pytest.raises(MexcAuthError):
        c.user.email()
