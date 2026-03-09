"""Pluggable HTTP transport layer."""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

import requests


class TransportError(Exception):
    """Raised when an HTTP-level or network-level error occurs."""


class HttpResponse:
    """Thin wrapper around an HTTP response."""

    def __init__(self, status_code: int, headers: dict[str, str], body: Any) -> None:
        self.status_code = status_code
        self.headers = headers
        self.body = body

    @property
    def ok(self) -> bool:
        return 200 <= self.status_code < 300


class Transport(ABC):
    """Protocol / base class for HTTP transports.

    Implementations must be reusable across multiple requests.
    """

    @abstractmethod
    def send(
        self,
        method: str,
        url: str,
        *,
        headers: dict[str, str] | None = None,
        json: Any = None,
        params: dict[str, str] | None = None,
        timeout: float = 30.0,
    ) -> HttpResponse:
        """Send an HTTP request and return an :class:`HttpResponse`.

        Raises:
            TransportError: On network or connection failure.
        """


class RequestsTransport(Transport):
    """Default transport backed by :mod:`requests`.

    A single :class:`requests.Session` is reused for connection pooling.
    """

    def __init__(self, session: requests.Session | None = None) -> None:
        self._session = session or requests.Session()

    def send(
        self,
        method: str,
        url: str,
        *,
        headers: dict[str, str] | None = None,
        json: Any = None,
        params: dict[str, str] | None = None,
        timeout: float = 30.0,
    ) -> HttpResponse:
        try:
            resp = self._session.request(
                method,
                url,
                headers=headers,
                json=json,
                params=params,
                timeout=timeout,
            )
        except requests.RequestException as exc:
            raise TransportError(str(exc)) from exc

        try:
            body = resp.json()
        except ValueError:
            body = resp.text

        return HttpResponse(
            status_code=resp.status_code,
            headers=dict(resp.headers),
            body=body,
        )
