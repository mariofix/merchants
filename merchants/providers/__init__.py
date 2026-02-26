"""Pluggable provider integrations."""

from __future__ import annotations

from abc import ABC, abstractmethod
from decimal import Decimal
from typing import Any

from pydantic import BaseModel

from merchants.models import CheckoutSession, PaymentState, PaymentStatus, WebhookEvent


class UserError(Exception):
    """Raised when a provider returns a user-level / validation error."""

    def __init__(self, message: str, code: str | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.code = code


class ProviderInfo(BaseModel):
    """Structured metadata for a payment provider.

    Downstream applications can use this model to introspect the provider
    registry — e.g. serialise to JSON, render in a UI, or drive routing logic.

    Attributes:
        key: Short machine-readable identifier (e.g. ``"stripe"``).
        name: Human-readable provider name (e.g. ``"Stripe"``).
        author: Author or maintainer of the provider integration.
        version: Version string for this provider integration.
        description: Short description of the provider.
        url: Documentation or homepage URL for the provider.
    """

    key: str
    name: str
    author: str
    version: str
    description: str = ""
    url: str = ""


class Provider(ABC):
    """Abstract base class for payment provider integrations."""

    #: Short machine-readable identifier, e.g. ``"stripe"``.
    key: str = "base"
    #: Human-readable provider name, e.g. ``"Stripe"``.
    name: str = "Base"
    #: Author or maintainer of this provider integration.
    author: str = ""
    #: Version string for this provider integration.
    version: str = "0.0.0"
    #: Short description of the provider.
    description: str = ""
    #: Documentation or homepage URL.
    url: str = ""

    def get_info(self) -> ProviderInfo:
        """Return a :class:`ProviderInfo` populated from this provider's class attributes."""
        return ProviderInfo(
            key=self.key,
            name=self.name,
            author=self.author,
            version=self.version,
            description=self.description,
            url=self.url,
        )

    @abstractmethod
    def create_checkout(
        self,
        amount: Decimal,
        currency: str,
        success_url: str,
        cancel_url: str,
        metadata: dict[str, Any] | None = None,
    ) -> CheckoutSession:
        """Create a hosted-checkout session.

        Returns:
            :class:`~merchants.models.CheckoutSession` with a ``redirect_url``.

        Raises:
            :class:`UserError`: If the provider returns an error response.
        """

    @abstractmethod
    def get_payment(self, payment_id: str) -> PaymentStatus:
        """Retrieve and normalise the status of a payment.

        Returns:
            :class:`~merchants.models.PaymentStatus` with a normalised
            :class:`~merchants.models.PaymentState`.
        """

    @abstractmethod
    def parse_webhook(self, payload: bytes, headers: dict[str, str]) -> WebhookEvent:
        """Parse and normalise a raw webhook payload.

        Returns:
            :class:`~merchants.models.WebhookEvent`.
        """


# ---------------------------------------------------------------------------
# Provider registry
# ---------------------------------------------------------------------------

_REGISTRY: dict[str, Provider] = {}


def register_provider(provider: Provider) -> None:
    """Register a provider instance under its :attr:`~Provider.key`."""
    _REGISTRY[provider.key] = provider


def get_provider(key_or_instance: str | Provider) -> Provider:
    """Return a provider by string key or pass through a Provider instance.

    Raises:
        KeyError: If ``key_or_instance`` is a string not found in the registry.
    """
    if isinstance(key_or_instance, Provider):
        return key_or_instance
    try:
        return _REGISTRY[key_or_instance]
    except KeyError:
        available = list(_REGISTRY.keys())
        raise KeyError(
            f"Provider {key_or_instance!r} not registered. " f"Available: {available}"
        ) from None


def list_providers() -> list[str]:
    """Return the keys of all registered providers."""
    return list(_REGISTRY.keys())


def describe_providers() -> list[ProviderInfo]:
    """Return :class:`ProviderInfo` for every registered provider.

    Downstream applications can use this to inspect the registry without
    knowing provider implementation details.
    """
    return [p.get_info() for p in _REGISTRY.values()]


# ---------------------------------------------------------------------------
# Normalisation helpers (shared across providers)
# ---------------------------------------------------------------------------

_STATE_MAP: dict[str, PaymentState] = {
    # Stripe-style
    "requires_payment_method": PaymentState.PENDING,
    "requires_confirmation": PaymentState.PENDING,
    "requires_action": PaymentState.PENDING,
    "processing": PaymentState.PROCESSING,
    "succeeded": PaymentState.SUCCEEDED,
    "canceled": PaymentState.CANCELLED,
    "cancelled": PaymentState.CANCELLED,
    "failed": PaymentState.FAILED,
    # PayPal-style
    "created": PaymentState.PENDING,
    "approved": PaymentState.PROCESSING,
    "completed": PaymentState.SUCCEEDED,
    "voided": PaymentState.CANCELLED,
    "refunded": PaymentState.REFUNDED,
    # Generic
    "pending": PaymentState.PENDING,
    "paid": PaymentState.SUCCEEDED,
    "success": PaymentState.SUCCEEDED,
    "successful": PaymentState.SUCCEEDED,
    "error": PaymentState.FAILED,
}


def normalise_state(raw_state: str) -> PaymentState:
    """Map a provider-specific status string to a :class:`~merchants.models.PaymentState`."""
    return _STATE_MAP.get(raw_state.lower(), PaymentState.UNKNOWN)
