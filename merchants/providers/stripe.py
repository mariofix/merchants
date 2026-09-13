"""Stripe-like provider stub demonstrating minor-unit amount handling."""

from __future__ import annotations

import json
import logging
from decimal import Decimal
from typing import Any

logger = logging.getLogger(__name__)
logger.setLevel("DEBUG")

from merchants.amount import from_minor_units, to_minor_units
from merchants.models import CheckoutSession, PaymentStatus, WebhookEvent
from merchants.providers import Provider, UserError, normalise_state
from merchants.transport import RequestsTransport, Transport

# Stripe uses 2 decimal places for most currencies (0 for JPY, etc.)
_ZERO_DECIMAL_CURRENCIES = {
    "jpy",
    "bif",
    "clp",
    "gnf",
    "mga",
    "pyg",
    "rwf",
    "ugx",
    "vnd",
    "xaf",
    "xof",
}


def _flatten_params(d: dict[str, Any], prefix: str = "") -> dict[str, Any]:
    """Flatten a nested dict into Stripe bracket-notation for form encoding."""
    out: dict[str, Any] = {}
    for k, v in d.items():
        key = f"{prefix}[{k}]" if prefix else k
        if isinstance(v, dict):
            out.update(_flatten_params(v, key))
        elif isinstance(v, list):
            for i, item in enumerate(v):
                if isinstance(item, dict):
                    out.update(_flatten_params(item, f"{key}[{i}]"))
                else:
                    out[f"{key}[{i}]"] = item
        else:
            out[key] = v
    return out


class StripeProvider(Provider):
    """StripeProvider for merchants-sdk (no stripe sdk).

    Demonstrates:
    - Converting amounts to/from minor units (cents).
    - ``Authorization: Bearer <key>`` auth header.
    - Stripe-style status strings in state normalisation.

    Args:
        api_key: Stripe secret key (``sk_test_…``).
        base_url: Override for testing; defaults to ``"https://api.stripe.com"``.
        transport: Optional custom transport.
    """

    key = "stripe"
    name = "Stripe"
    author = "mariofix"
    version = "2026.9.1"
    description = "Stripe payment gateway integration (stub). Converts amounts to minor units (cents)."
    url = "https://docs.stripe.com"
    config_required = {"api_key": "STRIPE_API_KEY"}  # nosec B105 -- config key name, not a credential value
    checkout_fields = {"email": "customer_email"}

    def __init__(
        self,
        api_key: str,
        base_url: str = "https://api.stripe.com",
        *,
        transport: Transport | None = None,
    ) -> None:
        logger.debug("stripe.py: StripeProvider.__init__ called")
        self._api_key = api_key
        self._base_url = base_url.rstrip("/")
        self._transport = transport or RequestsTransport()

    def _headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self._api_key}"}

    def _currency_decimals(self, currency: str) -> int:
        return 0 if currency.lower() in _ZERO_DECIMAL_CURRENCIES else 2

    def create_checkout(
        self,
        amount: Decimal,
        currency: str,
        success_url: str,
        cancel_url: str,
        metadata: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> CheckoutSession:
        logger.debug(f"stripe.py: StripeProvider.create_checkout called with {amount=} {currency=}")
        decimals = self._currency_decimals(currency)
        unit_amount = to_minor_units(amount, decimals=decimals)
        payload: dict[str, Any] = {
            "payment_method_types": ["card"],
            "line_items": [
                {
                    "price_data": {
                        "currency": currency.lower(),
                        "unit_amount": unit_amount,
                        "product_data": {"name": "Order"},
                    },
                    "quantity": 1,
                }
            ],
            "mode": "payment",
            "success_url": success_url,
            "cancel_url": cancel_url,
            "metadata": metadata or {},
        }
        logger.debug(f"stripe.py: StripeProvider.create_checkout.checkout_session {payload=}")
        resp = self._transport.send(
            "POST",
            f"{self._base_url}/v1/checkout/sessions",
            headers=self._headers(),
            data=_flatten_params(payload),
        )
        logger.debug(f"stripe.py: StripeProvider.create_checkout.checkout_session {resp=}")
        if not resp.ok:
            body_msg = resp.body.get("error", {}).get("message", "") if isinstance(resp.body, dict) else ""
            raise UserError(
                body_msg or f"Stripe error {resp.status_code}",
                code=str(resp.status_code),
            )

        body: dict[str, Any] = resp.body if isinstance(resp.body, dict) else {}
        return CheckoutSession(
            session_id=str(body.get("id", "")),
            redirect_url=str(body.get("url", "")),
            provider=self.key,
            amount=amount,
            currency=currency,
            metadata=metadata or {},
            raw=body,
        )

    def get_payment(self, payment_id: str) -> PaymentStatus:
        logger.debug(f"stripe.py: StripeProvider.get_payment called with {payment_id=}")
        resp = self._transport.send(
            "GET",
            f"{self._base_url}/v1/checkout/sessions/{payment_id}",
            headers=self._headers(),
        )
        body: dict[str, Any] = resp.body if isinstance(resp.body, dict) else {}
        raw_state = str(body.get("status", "unknown"))
        currency = str(body.get("currency", ""))
        amount_minor = body.get("amount")
        decimals = self._currency_decimals(currency)
        amount_decimal = from_minor_units(int(amount_minor), decimals=decimals) if amount_minor is not None else None
        return PaymentStatus(
            payment_id=payment_id,
            state=normalise_state(raw_state),
            provider=self.key,
            amount=amount_decimal,
            currency=currency or None,
            raw=body,
        )

    def parse_webhook(self, payload: bytes, headers: dict[str, str]) -> WebhookEvent:
        logger.debug("stripe.py: StripeProvider.parse_webhook called")

        try:
            data: dict[str, Any] = json.loads(payload)
        except ValueError:
            data = {}
        event_type = str(data.get("type", "unknown"))
        obj = data.get("data", {}).get("object", {})
        raw_state = str(obj.get("status", "unknown"))
        payment_id = obj.get("id") or obj.get("payment_intent")
        return WebhookEvent(
            event_id=data.get("id"),
            event_type=event_type,
            payment_id=payment_id,
            state=normalise_state(raw_state),
            provider=self.key,
            raw=data,
        )
