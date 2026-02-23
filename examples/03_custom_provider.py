"""
Example 3 – Building your own provider
========================================

Implement the ``Provider`` ABC to integrate any payment gateway.

This example shows a minimal provider for a fictitious gateway called "AcmePay"
that accepts JSON over HTTPS.
"""
from __future__ import annotations

import json
from decimal import Decimal
from typing import Any

import merchants
from merchants.models import CheckoutSession, PaymentState, PaymentStatus, WebhookEvent
from merchants.providers import Provider, UserError, normalise_state, register_provider
from merchants.transport import RequestsTransport, Transport


class AcmePayProvider(Provider):
    """Custom provider for the AcmePay fictitious gateway.

    Demonstrates:
    - Wrapping a JSON REST API.
    - Raising ``UserError`` on non-2xx responses.
    - Mapping provider-specific status strings to ``PaymentState``.
    - Parsing an incoming webhook payload.
    """

    key = "acmepay"

    # AcmePay-specific status → canonical PaymentState
    _STATE_MAP: dict[str, PaymentState] = {
        "WAITING": PaymentState.PENDING,
        "PROCESSING": PaymentState.PROCESSING,
        "APPROVED": PaymentState.SUCCEEDED,
        "DECLINED": PaymentState.FAILED,
        "VOIDED": PaymentState.CANCELLED,
        "REFUNDED": PaymentState.REFUNDED,
    }

    def __init__(
        self,
        api_key: str,
        base_url: str = "https://api.acmepay.example.com",
        *,
        transport: Transport | None = None,
    ) -> None:
        self._api_key = api_key
        self._base_url = base_url.rstrip("/")
        self._transport = transport or RequestsTransport()

    def _headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self._api_key}", "Content-Type": "application/json"}

    def create_checkout(
        self,
        amount: Decimal,
        currency: str,
        success_url: str,
        cancel_url: str,
        metadata: dict[str, Any] | None = None,
    ) -> CheckoutSession:
        resp = self._transport.send(
            "POST",
            f"{self._base_url}/v1/sessions",
            headers=self._headers(),
            json={
                "amount": str(amount),
                "currency": currency.upper(),
                "success_url": success_url,
                "cancel_url": cancel_url,
                "metadata": metadata or {},
            },
        )
        if not resp.ok:
            msg = resp.body.get("error", "") if isinstance(resp.body, dict) else ""
            raise UserError(msg or f"AcmePay error {resp.status_code}", code=str(resp.status_code))

        body: dict[str, Any] = resp.body if isinstance(resp.body, dict) else {}
        return CheckoutSession(
            session_id=str(body["id"]),
            redirect_url=str(body["checkout_url"]),
            provider=self.key,
            amount=amount,
            currency=currency,
            metadata=metadata or {},
            raw=body,
        )

    def get_payment(self, payment_id: str) -> PaymentStatus:
        resp = self._transport.send(
            "GET",
            f"{self._base_url}/v1/payments/{payment_id}",
            headers=self._headers(),
        )
        body: dict[str, Any] = resp.body if isinstance(resp.body, dict) else {}
        raw_state = str(body.get("status", ""))
        state = self._STATE_MAP.get(raw_state.upper(), normalise_state(raw_state))
        return PaymentStatus(
            payment_id=payment_id,
            state=state,
            provider=self.key,
            raw=body,
        )

    def parse_webhook(self, payload: bytes, headers: dict[str, str]) -> WebhookEvent:
        try:
            data: dict[str, Any] = json.loads(payload)
        except ValueError:
            data = {}
        raw_state = str(data.get("status", ""))
        state = self._STATE_MAP.get(raw_state.upper(), normalise_state(raw_state))
        return WebhookEvent(
            event_id=data.get("event_id"),
            event_type=str(data.get("event_type", "payment.update")),
            payment_id=data.get("payment_id"),
            state=state,
            provider=self.key,
            raw=data,
        )


# ---------------------------------------------------------------------------
# Register and use the custom provider
# ---------------------------------------------------------------------------

# Register globally so it can be selected by key string
register_provider(AcmePayProvider(api_key="acme_test_key"))

# Create a client using the string key
client = merchants.Client(provider="acmepay")
print("Using provider:", client._provider.key)

# Or instantiate directly
client2 = merchants.Client(provider=AcmePayProvider(api_key="acme_test_key"))
print("Using provider:", client2._provider.key)
