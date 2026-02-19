"""Pluggable HTTP transport layer.

The default transport uses :mod:`requests`.  Custom transports must implement
:class:`BaseTransport`.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class BaseTransport(ABC):
    """Abstract base class for HTTP transports."""

    @abstractmethod
    def request(
        self,
        method: str,
        url: str,
        *,
        headers: dict[str, str] | None = None,
        json: Any = None,
        data: bytes | None = None,
        timeout: float = 30.0,
    ) -> "TransportResponse":
        """Send an HTTP request and return a :class:`TransportResponse`."""


class TransportResponse:
    """Thin wrapper around an HTTP response."""

    def __init__(self, status_code: int, body: bytes, headers: dict[str, str]) -> None:
        self.status_code = status_code
        self.body = body
        self.headers = headers

    def json(self) -> Any:
        import json

        return json.loads(self.body)

    def raise_for_status(self) -> None:
        from merchants.errors import TransportError

        if self.status_code >= 400:
            raise TransportError(
                f"HTTP {self.status_code}",
                status_code=self.status_code,
            )


class RequestsTransport(BaseTransport):
    """Default transport backed by :mod:`requests`."""

    def request(
        self,
        method: str,
        url: str,
        *,
        headers: dict[str, str] | None = None,
        json: Any = None,
        data: bytes | None = None,
        timeout: float = 30.0,
    ) -> TransportResponse:
        import requests

        resp = requests.request(
            method,
            url,
            headers=headers or {},
            json=json,
            data=data,
            timeout=timeout,
        )
        return TransportResponse(
            status_code=resp.status_code,
            body=resp.content,
            headers=dict(resp.headers),
        )
