"""Auth strategies for the merchants SDK."""
from __future__ import annotations

from abc import ABC, abstractmethod


class AuthStrategy(ABC):
    """Base class for authentication strategies."""

    @abstractmethod
    def apply(self, headers: dict[str, str]) -> dict[str, str]:
        """Mutate and return the request headers with auth applied."""


class ApiKeyAuth(AuthStrategy):
    """Sends a static API key in a configurable request header.

    Args:
        api_key: The API key value.
        header: Header name to use (default: ``"X-Api-Key"``).
    """

    def __init__(self, api_key: str, header: str = "X-Api-Key") -> None:
        self._api_key = api_key
        self._header = header

    def apply(self, headers: dict[str, str]) -> dict[str, str]:
        headers[self._header] = self._api_key
        return headers


class TokenAuth(AuthStrategy):
    """Sends a bearer-style token in a configurable header.

    Args:
        token: The token value.
        header: Header name (default: ``"Authorization"``).
        scheme: Prefix placed before the token (default: ``"Bearer"``).
    """

    def __init__(
        self,
        token: str,
        header: str = "Authorization",
        scheme: str = "Bearer",
    ) -> None:
        self._token = token
        self._header = header
        self._scheme = scheme

    def apply(self, headers: dict[str, str]) -> dict[str, str]:
        headers[self._header] = f"{self._scheme} {self._token}"
        return headers
