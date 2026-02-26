"""PayPal-like provider stub demonstrating decimal-string amount handling."""

from __future__ import annotations

import json
from decimal import Decimal
from typing import Any

from merchants.amount import to_decimal_string
from merchants.models import CheckoutSession, PaymentStatus, WebhookEvent
from merchants.providers import Provider, UserError, normalise_state
from merchants.transport import RequestsTransport, Transport


class PayPalProvider(Provider):
    """PayPal-like provider stub.

    Demonstrates:
    - Sending amounts as decimal strings (e.g. ``"19.99"``).
    - ``Authorization: Bearer <token>`` auth header.
    - PayPal-style status strings in state normalisation.

    .. note::
        This is a stub – it does not call the real PayPal API.
        Replace ``base_url`` and inject a real transport to connect to PayPal.

    Args:
        access_token: OAuth access token.
        base_url: Override for testing; defaults to ``"https://api-m.paypal.com"``.
        transport: Optional custom transport.
    """

    key = "paypal"
    name = "PayPal"
    author = "merchants team"
    version = "1.0.0"
    description = (
        "PayPal payment gateway integration (stub). Sends amounts as decimal strings."
    )
    url = "https://developer.paypal.com"

    def __init__(
        self,
        access_token: str,
        base_url: str = "https://api-m.paypal.com",
        *,
        transport: Transport | None = None,
    ) -> None:
        self._access_token = access_token
        self._base_url = base_url.rstrip("/")
        self._transport = transport or RequestsTransport()

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self._access_token}",
            "Content-Type": "application/json",
        }

    def create_checkout(
        self,
        amount: Decimal,
        currency: str,
        success_url: str,
        cancel_url: str,
        metadata: dict[str, Any] | None = None,
    ) -> CheckoutSession:
        payload: dict[str, Any] = {
            "intent": "CAPTURE",
            "purchase_units": [
                {
                    "amount": {
                        "currency_code": currency.upper(),
                        "value": to_decimal_string(amount),
                    }
                }
            ],
            "application_context": {
                "return_url": success_url,
                "cancel_url": cancel_url,
            },
        }
        resp = self._transport.send(
            "POST",
            f"{self._base_url}/v2/checkout/orders",
            headers=self._headers(),
            json=payload,
        )
        if not resp.ok:
            body_msg = (
                resp.body.get("message", "") if isinstance(resp.body, dict) else ""
            )
            raise UserError(
                body_msg or f"PayPal error {resp.status_code}",
                code=str(resp.status_code),
            )

        body: dict[str, Any] = resp.body if isinstance(resp.body, dict) else {}
        redirect_url = ""
        for link in body.get("links", []):
            if link.get("rel") == "approve":
                redirect_url = link.get("href", "")
                break

        return CheckoutSession(
            session_id=str(body.get("id", "")),
            redirect_url=redirect_url,
            provider=self.key,
            amount=amount,
            currency=currency,
            metadata=metadata or {},
            raw=body,
        )

    def get_payment(self, payment_id: str) -> PaymentStatus:
        resp = self._transport.send(
            "GET",
            f"{self._base_url}/v2/checkout/orders/{payment_id}",
            headers=self._headers(),
        )
        body: dict[str, Any] = resp.body if isinstance(resp.body, dict) else {}
        raw_state = str(body.get("status", "unknown"))
        pu = body.get("purchase_units", [{}])
        amount_info = pu[0].get("amount", {}) if pu else {}
        currency = amount_info.get("currency_code")
        amount_val = amount_info.get("value")
        amount_decimal = Decimal(str(amount_val)) if amount_val is not None else None
        return PaymentStatus(
            payment_id=payment_id,
            state=normalise_state(raw_state),
            provider=self.key,
            amount=amount_decimal,
            currency=currency,
            raw=body,
        )

    def parse_webhook(self, payload: bytes, headers: dict[str, str]) -> WebhookEvent:
        try:
            data: dict[str, Any] = json.loads(payload)
        except ValueError:
            data = {}
        event_type = str(data.get("event_type", "unknown"))
        resource = data.get("resource", {})
        raw_state = str(resource.get("status", "unknown"))
        payment_id = resource.get("id")
        return WebhookEvent(
            event_id=data.get("id"),
            event_type=event_type,
            payment_id=payment_id,
            state=normalise_state(raw_state),
            provider=self.key,
            raw=data,
        )
