"""Generic HTTP provider – calls arbitrary REST endpoints."""

from __future__ import annotations

from decimal import Decimal
from typing import Any

from merchants.amount import to_decimal_string
from merchants.models import CheckoutSession, PaymentState, PaymentStatus, WebhookEvent
from merchants.providers import Provider, UserError, normalise_state
from merchants.transport import RequestsTransport, Transport


class GenericProvider(Provider):
    """A minimal HTTP provider that POST/GET against configurable endpoints.

    This is useful for custom or in-house payment gateways that follow a
    simple REST interface.

    Args:
        checkout_url: Endpoint to ``POST`` for creating a checkout session.
        payment_url_template: URL template with ``{payment_id}`` placeholder
            for fetching payment status.
        transport: Optional custom :class:`~merchants.transport.Transport`.
    """

    key = "generic"
    name = "Generic"
    author = "merchants team"
    version = "1.0.0"
    description = (
        "Generic REST endpoint provider for custom or in-house payment gateways."
    )
    url = ""

    def __init__(
        self,
        checkout_url: str,
        payment_url_template: str,
        *,
        transport: Transport | None = None,
        extra_headers: dict[str, str] | None = None,
    ) -> None:
        self._checkout_url = checkout_url
        self._payment_url_template = payment_url_template
        self._transport = transport or RequestsTransport()
        self._extra_headers = extra_headers or {}

    def create_checkout(
        self,
        amount: Decimal,
        currency: str,
        success_url: str,
        cancel_url: str,
        metadata: dict[str, Any] | None = None,
    ) -> CheckoutSession:
        payload: dict[str, Any] = {
            "amount": to_decimal_string(amount),
            "currency": currency.upper(),
            "success_url": success_url,
            "cancel_url": cancel_url,
            "metadata": metadata or {},
        }
        resp = self._transport.send(
            "POST",
            self._checkout_url,
            headers=self._extra_headers,
            json=payload,
        )
        if not resp.ok:
            raise UserError(
                f"Provider returned {resp.status_code}", code=str(resp.status_code)
            )

        body: dict[str, Any] = resp.body if isinstance(resp.body, dict) else {}
        return CheckoutSession(
            session_id=str(body.get("id", "")),
            redirect_url=str(body.get("redirect_url", "")),
            provider=self.key,
            amount=amount,
            currency=currency,
            metadata=metadata or {},
            raw=body,
        )

    def get_payment(self, payment_id: str) -> PaymentStatus:
        url = self._payment_url_template.format(payment_id=payment_id)
        resp = self._transport.send("GET", url, headers=self._extra_headers)
        body: dict[str, Any] = resp.body if isinstance(resp.body, dict) else {}
        raw_state = str(body.get("status", "unknown"))
        return PaymentStatus(
            payment_id=payment_id,
            state=normalise_state(raw_state),
            provider=self.key,
            raw=body,
        )

    def parse_webhook(self, payload: bytes, headers: dict[str, str]) -> WebhookEvent:
        import json

        try:
            data: dict[str, Any] = json.loads(payload)
        except ValueError:
            data = {}
        raw_state = str(data.get("status", "unknown"))
        return WebhookEvent(
            event_id=data.get("event_id"),
            event_type=str(data.get("event_type", "unknown")),
            payment_id=data.get("payment_id"),
            state=normalise_state(raw_state),
            provider=self.key,
            raw=data,
        )
