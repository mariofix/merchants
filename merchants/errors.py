"""SDK error types."""

from __future__ import annotations


class MerchantsError(Exception):
    """Base error for the merchants SDK."""


class TransportError(MerchantsError):
    """Raised when an HTTP transport failure occurs (network, non-2xx response)."""

    def __init__(self, message: str, status_code: int | None = None) -> None:
        super().__init__(message)
        self.status_code = status_code


class ProviderError(MerchantsError):
    """Raised when a provider-level error occurs."""


class ProviderNotFoundError(MerchantsError):
    """Raised when a requested provider is not registered."""

    def __init__(self, name: str) -> None:
        super().__init__(f"Provider '{name}' is not registered.")
        self.name = name


class WebhookVerificationError(MerchantsError):
    """Raised when HMAC webhook signature verification fails."""


class ParseError(MerchantsError):
    """Raised or returned as Failure when payload parsing/validation fails."""
