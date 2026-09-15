"""PayPal-like provider stub demonstrating decimal-string amount handling."""

from __future__ import annotations

import json
import logging
from decimal import Decimal
from typing import Any

from merchants.amount import to_decimal_string
from merchants.models import CheckoutSession, PaymentStatus, WebhookEvent
from merchants.providers import Provider, UserError, normalise_state
from merchants.transport import RequestsTransport, Transport

logger = logging.getLogger(__name__)


class PayPalProvider(Provider):
    """PayPalProvider for merchants-sdk (no paypalserversdk).

    Demonstrates:
    - Sending amounts as decimal strings (e.g. ``"19.99"``).
    - ``Authorization: Bearer <token>`` auth header.
    - PayPal-style status strings in state normalisation.

    Args:
        access_token: OAuth access token.
        base_url: Override for testing; defaults to ``"https://api-m.paypal.com"``.
        transport: Optional custom transport.
    """

    key = "paypal"
    name = "PayPal"
    author = "mariofix"
    version = "2026.9.1"
    description = "PayPal payment gateway integration. Sends amounts as decimal strings."
    url = "https://developer.paypal.com"
    config_required = {
        "client_id": "PAYPAL_CLIENT_ID",  # nosec B105 -- config key name, not a credential value
        "secret_key": "PAYPAL_SECRET_KEY",  # nosec B105 -- config key name, not a credential value
        "base_url": "PAYPAL_BASE_URL",
    }
    checkout_fields = {"email": "email"}

    def __init__(
        self,
        client_id: str,
        secret_key: str,
        base_url: str = "https://api-m.paypal.com",
        *,
        transport: Transport | None = None,
    ) -> None:
        logger.debug("paypal.py: PaypalProvider.__init__ called")
        self._client_id = client_id
        self._secret_key = secret_key
        self._base_url = base_url.rstrip("/")
        self._transport = transport or RequestsTransport()

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self._get_token()}",
            "Content-Type": "application/json",
        }

    def _get_token(self) -> str:
        """Creates a PayPal bearer token"""
        logger.debug("paypal.py: PaypalProvider._get_token called")
        resp = self._transport.send(
            "POST",
            f"{self._base_url}/v1/oauth2/token",
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            data={"grant_type": "client_credentials"},
            auth=(self._client_id, self._secret_key),
        )
        logger.debug(f"paypal.py: PaypalProvider._get_token {resp=}")

        if not resp.ok:
            raise UserError(f"paypal.py: PaypalProvider._get_token {resp.ok=}")
        
        body: dict[str, Any] = resp.body if isinstance(resp.body, dict) else {}
        self._access_token = body.get("access_token", False)
        return self._access_token

    def create_checkout(
        self,
        amount: Decimal,
        currency: str,
        success_url: str,
        cancel_url: str,
        metadata: dict[str, Any] | None = None,
        shipping: str = "NO_SHIPPING",
        **kwargs: Any,
    ) -> CheckoutSession:
        payload: dict[str, Any] = {
            "intent": "CAPTURE",
            "purchase_units": [
                {
                    "amount": {
                        "currency_code": currency.upper(),
                        "value": to_decimal_string(amount),
                    },
                    "custom_id": metadata.get("slug") if metadata else None,
                    "description": metadata.get("description") if metadata else None,
                }
            ],
            "payer": {"email_address": kwargs.get("email")},
            "processing_instruction": "ORDER_COMPLETE_ON_PAYMENT_APPROVAL",
            "application_context": {
                "return_url": success_url,
                "user_action": "PAY_NOW",
                "cancel_url": cancel_url,
                "shipping_preference": shipping,
                "landing_page": "BILLING",
            },
        }
        logger.debug(f"paypal.py: PayPalProvider.create_checkout {payload=}")
        resp = self._transport.send(
            "POST",
            f"{self._base_url}/v2/checkout/orders",
            headers=self._headers(),
            json=payload,
        )
        if not resp.ok:
            body_msg = resp.body.get("message", "") if isinstance(resp.body, dict) else ""
            raise UserError(
                body_msg or f"PayPal error {resp.status_code}",
                code=str(resp.status_code),
            )

        body: dict[str, Any] = resp.body if isinstance(resp.body, dict) else {}
        redirect_url = next(link["href"] for link in body.get("links", []) if link["rel"] == "approve")

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
