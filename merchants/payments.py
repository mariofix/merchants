"""Payment models (Pydantic) and state enum."""

from __future__ import annotations

import enum
from typing import Any

from pydantic import BaseModel


class PaymentState(str, enum.Enum):
    """Normalized payment lifecycle states."""

    PENDING = "PENDING"
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"
    CANCELED = "CANCELED"
    UNKNOWN = "UNKNOWN"


class CheckoutSession(BaseModel):
    """Represents a newly created hosted-checkout session."""

    id: str
    redirect_url: str
    raw: dict[str, Any] = {}


class PaymentStatus(BaseModel):
    """Normalized payment status returned by the provider."""

    id: str
    state: PaymentState
    failure_reason: str | None = None
    raw: dict[str, Any] = {}

    @property
    def is_final(self) -> bool:
        """Return ``True`` if the payment has reached a terminal state."""
        return self.state in {PaymentState.SUCCEEDED, PaymentState.FAILED, PaymentState.CANCELED}

    @property
    def is_success(self) -> bool:
        """Return ``True`` if the payment succeeded."""
        return self.state == PaymentState.SUCCEEDED
