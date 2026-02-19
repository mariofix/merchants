"""Mock provider – for testing and local development (no network calls)."""

from __future__ import annotations

import secrets
from decimal import Decimal

from merchants.amount import to_decimal_string
from merchants.payments import CheckoutSession, PaymentState, PaymentStatus
from merchants.providers.base import BaseProvider


class MockProvider(BaseProvider):
    """In-memory mock provider that never makes network calls.

    Useful for unit tests and local development.  Every checkout session
    succeeds immediately; you can override ``default_state`` at construction
    time to simulate other outcomes.
    """

    def __init__(self, default_state: PaymentState = PaymentState.SUCCEEDED) -> None:
        self.default_state = default_state
        self._sessions: dict[str, PaymentStatus] = {}

    def create_checkout(
        self,
        amount: Decimal,
        currency: str,
        *,
        return_url: str,
        **kwargs,
    ) -> CheckoutSession:
        session_id = f"mock_{secrets.token_hex(8)}"
        raw = {
            "id": session_id,
            "amount": to_decimal_string(amount),
            "currency": currency,
            "return_url": return_url,
        }
        status = PaymentStatus(id=session_id, state=self.default_state, raw=raw)
        self._sessions[session_id] = status
        return CheckoutSession(
            id=session_id,
            redirect_url=f"https://mock.example.com/pay/{session_id}",
            raw=raw,
        )

    def get_payment(self, payment_id: str) -> PaymentStatus:
        if payment_id in self._sessions:
            return self._sessions[payment_id]
        return PaymentStatus(
            id=payment_id,
            state=PaymentState.UNKNOWN,
            raw={"id": payment_id},
        )
