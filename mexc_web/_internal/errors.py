"""Exception hierarchy for the MEXC web-token SDK."""

from __future__ import annotations

from typing import Any

__all__ = [
    "MexcError",
    "MexcAuthError",
    "MexcHTTPError",
    "MexcAPIError",
]


class MexcError(Exception):
    """Base class for every error raised by this library."""


class MexcAuthError(MexcError):
    """Raised when a private endpoint is called without a web token."""


class MexcHTTPError(MexcError):
    """Raised on a non-2xx HTTP response (transport-level failure).

    Attributes:
        status: HTTP status code.
        body: Raw response body (text), truncated for readability.
    """

    def __init__(self, status: int, body: str) -> None:
        self.status = status
        self.body = body
        super().__init__(f"HTTP {status}: {body[:500]}")


class MexcAPIError(MexcError):
    """Raised when MEXC returns ``success: false`` (application-level failure).

    Attributes:
        code: MEXC business error code (0 == success).
        message: Human-readable message returned by MEXC.
        response: The full decoded JSON response.
    """

    def __init__(self, code: Any, message: str, response: dict[str, Any]) -> None:
        self.code = code
        self.message = message
        self.response = response
        super().__init__(f"MEXC error {code}: {message}")
