"""Pydantic models for the merchants SDK."""

from __future__ import annotations

from decimal import Decimal
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class PaymentState(str, Enum):
    """Normalised payment lifecycle states."""

    PENDING = "pending"
    PROCESSING = "processing"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"
    UNKNOWN = "unknown"


class CheckoutSession(BaseModel):
    """A hosted-checkout session returned by a provider."""

    session_id: str
    redirect_url: str
    provider: str
    amount: Decimal
    currency: str
    metadata: dict[str, Any] = Field(default_factory=dict)
    raw: dict[str, Any] = Field(default_factory=dict)


class PaymentStatus(BaseModel):
    """Normalised status of a payment retrieved from a provider."""

    payment_id: str
    state: PaymentState
    provider: str
    amount: Decimal | None = None
    currency: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    raw: dict[str, Any] = Field(default_factory=dict)

    @property
    def is_final(self) -> bool:
        """Return True when no further state transitions are expected."""
        return self.state in (
            PaymentState.SUCCEEDED,
            PaymentState.FAILED,
            PaymentState.CANCELLED,
            PaymentState.REFUNDED,
        )

    @property
    def is_success(self) -> bool:
        """Return True only when the payment definitively succeeded."""
        return self.state is PaymentState.SUCCEEDED


class WebhookEvent(BaseModel):
    """Parsed, normalised webhook event from a provider."""

    event_id: str | None = None
    event_type: str
    payment_id: str | None = None
    state: PaymentState = PaymentState.UNKNOWN
    provider: str = "unknown"
    raw: dict[str, Any] = Field(default_factory=dict)
