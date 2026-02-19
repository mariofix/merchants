"""Auth strategy helpers.

Auth strategies add authentication information (headers, query params, …) to
outgoing requests.  Implement :class:`BaseAuth` to create a custom strategy.
"""

from __future__ import annotations

from abc import ABC, abstractmethod


class BaseAuth(ABC):
    """Abstract base for authentication strategies."""

    @abstractmethod
    def apply(self, headers: dict[str, str]) -> dict[str, str]:
        """Return *headers* updated with authentication information."""


class BearerTokenAuth(BaseAuth):
    """HTTP ``Authorization: Bearer <token>`` header."""

    def __init__(self, token: str) -> None:
        self.token = token

    def apply(self, headers: dict[str, str]) -> dict[str, str]:
        return {**headers, "Authorization": f"Bearer {self.token}"}


class ApiKeyAuth(BaseAuth):
    """Arbitrary API-key header (e.g., ``X-Api-Key``)."""

    def __init__(self, header_name: str, api_key: str) -> None:
        self.header_name = header_name
        self.api_key = api_key

    def apply(self, headers: dict[str, str]) -> dict[str, str]:
        return {**headers, self.header_name: self.api_key}


class NoAuth(BaseAuth):
    """No-op auth – passes headers through unchanged."""

    def apply(self, headers: dict[str, str]) -> dict[str, str]:
        return headers
