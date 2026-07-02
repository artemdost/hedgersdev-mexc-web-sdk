"""Shared base for endpoint namespaces."""

from __future__ import annotations

from typing import Any

from .._internal.transport import Transport

__all__ = ["Namespace", "clean"]


def clean(params: dict[str, Any]) -> dict[str, Any]:
    """Drop ``None`` values so optional args don't leak into the request."""
    return {k: v for k, v in params.items() if v is not None}


class Namespace:
    """Thin wrapper binding a group of endpoints to the shared transport."""

    def __init__(self, transport: Transport) -> None:
        self._t = transport
