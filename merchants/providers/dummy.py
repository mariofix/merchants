"""Dummy provider – returns sensible random data for local dev and testing."""

from __future__ import annotations

import random
import string
import uuid
from decimal import Decimal
from typing import Any

from merchants.models import CheckoutSession, PaymentState, PaymentStatus, WebhookEvent
from merchants.providers import Provider


def _rand_id(prefix: str = "", length: int = 12) -> str:
    suffix = "".join(random.choices(string.ascii_lowercase + string.digits, k=length))
    return f"{prefix}{suffix}"


class DummyProvider(Provider):
    """Local development / testing provider.

    Returns plausible random data without hitting any real API.
    Useful for rapid iteration and unit-testing application code.

    Args:
        base_url: Fake base URL included in the redirect URL
            (default: ``"https://dummy-pay.example.com"``).
        always_state: If set, every :meth:`get_payment` call returns this
            :class:`~merchants.models.PaymentState` instead of a random one.
    """

    key = "dummy"
    name = "Dummy"
    author = "merchants team"
    version = "1.0.0"
    description = "Local development provider that returns random data without calling any real API."
    url = ""

    _TERMINAL_STATES = [
        PaymentState.SUCCEEDED,
        PaymentState.FAILED,
        PaymentState.CANCELLED,
    ]

    def __init__(
        self,
        base_url: str = "https://dummy-pay.example.com",
        *,
        always_state: PaymentState | None = None,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._always_state = always_state

    def create_checkout(
        self,
        amount: Decimal,
        currency: str,
        success_url: str,
        cancel_url: str,
        metadata: dict[str, Any] | None = None,
    ) -> CheckoutSession:
        session_id = _rand_id("dummy_sess_")
        return CheckoutSession(
            session_id=session_id,
            redirect_url=f"{self._base_url}/pay/{session_id}?amount={amount}&currency={currency}",
            provider=self.key,
            amount=amount,
            currency=currency,
            metadata=metadata or {},
            raw={"simulated": True},
        )

    def get_payment(self, payment_id: str) -> PaymentStatus:
        state = self._always_state or random.choice(self._TERMINAL_STATES)
        return PaymentStatus(
            payment_id=payment_id,
            state=state,
            provider=self.key,
            raw={"simulated": True},
        )

    def parse_webhook(self, payload: bytes, headers: dict[str, str]) -> WebhookEvent:
        import json

        try:
            data: dict[str, Any] = json.loads(payload)
        except ValueError:
            data = {}
        return WebhookEvent(
            event_id=data.get("event_id", _rand_id("dummy_evt_")),
            event_type=data.get("event_type", "payment.simulated"),
            payment_id=data.get("payment_id", _rand_id("dummy_pay_")),
            state=PaymentState.SUCCEEDED,
            provider=self.key,
            raw=data,
        )
