"""Khipu provider – wraps the ``khipu-tools`` package."""

from __future__ import annotations

import json
from decimal import Decimal
from typing import Any

from merchants.amount import to_decimal_string
from merchants.models import CheckoutSession, PaymentState, PaymentStatus, WebhookEvent
from merchants.providers import Provider, UserError

try:
    import khipu_tools
    from khipu_tools import KhipuClient
except ImportError as exc:  # pragma: no cover
    raise ImportError("khipu-tools is required for KhipuProvider. Install it with: pip install khipu-tools") from exc

# Khipu payment statuses
_KHIPU_STATE_MAP: dict[str, PaymentState] = {
    "pending": PaymentState.PENDING,
    "verifying": PaymentState.PROCESSING,
    "done": PaymentState.SUCCEEDED,
    "rejected": PaymentState.FAILED,
    "expired": PaymentState.CANCELLED,
    "reversed": PaymentState.REFUNDED,
}


class KhipuProvider(Provider):
    """Khipu payment provider.

    Uses the ``khipu-tools`` package to create and query payments on
    `Khipu <https://khipu.com>`_.

    Args:
        api_key: Khipu receiver API key.
        subject: Default payment subject / description sent to Khipu.
        notify_url: Webhook URL Khipu will call when the payment is confirmed.
    """

    key = "khipu"
    name = "Khipu"
    author = "merchants team"
    version = "1.0.0"
    description = "Khipu payment gateway for Chile, powered by khipu-tools."
    url = "https://khipu.com"

    def __init__(
        self,
        api_key: str,
        *,
        subject: str = "Order",
        notify_url: str = "",
    ) -> None:
        self._api_key = api_key
        self._subject = subject
        self._notify_url = notify_url

    def _client(self) -> KhipuClient:
        return KhipuClient(api_key=self._api_key)

    def create_checkout(
        self,
        amount: Decimal,
        currency: str,
        success_url: str,
        cancel_url: str,
        metadata: dict[str, Any] | None = None,
    ) -> CheckoutSession:
        params: dict[str, Any] = {
            "amount": to_decimal_string(amount),
            "currency": currency.upper(),
            "subject": self._subject,
            "return_url": success_url,
            "cancel_url": cancel_url,
            "notify_api_version": "3.0",
        }
        if self._notify_url:
            params["notify_url"] = self._notify_url
        if metadata and metadata.get("order_id"):
            params["transaction_id"] = str(metadata["order_id"])

        try:
            result = self._client().payments.create(**params)
        except Exception as exc:
            raise UserError(str(exc)) from exc

        payment_url = result.get("payment_url", "")
        payment_id = result.get("payment_id", "")
        return CheckoutSession(
            session_id=str(payment_id),
            redirect_url=str(payment_url),
            provider=self.key,
            amount=amount,
            currency=currency,
            metadata=metadata or {},
            raw=dict(result),
        )

    def get_payment(self, payment_id: str) -> PaymentStatus:
        try:
            result = self._client().payments.get(payment_id=payment_id)
        except Exception as exc:
            raise UserError(str(exc)) from exc

        raw_state = str(result.get("status", "pending"))
        state = _KHIPU_STATE_MAP.get(raw_state.lower(), PaymentState.UNKNOWN)
        amount_val = result.get("amount")
        currency = result.get("currency")
        return PaymentStatus(
            payment_id=payment_id,
            state=state,
            provider=self.key,
            amount=Decimal(str(amount_val)) if amount_val is not None else None,
            currency=currency,
            raw=dict(result),
        )

    def parse_webhook(self, payload: bytes, headers: dict[str, str]) -> WebhookEvent:
        try:
            data: dict[str, Any] = json.loads(payload)
        except ValueError:
            from urllib.parse import parse_qs

            qs = parse_qs(payload.decode(errors="replace"))
            data = {k: v[0] for k, v in qs.items()}

        payment_id = data.get("payment_id")
        raw_state = str(data.get("payment_status", "pending"))
        state = _KHIPU_STATE_MAP.get(raw_state.lower(), PaymentState.UNKNOWN)
        return WebhookEvent(
            event_id=payment_id,
            event_type="payment.notification",
            payment_id=payment_id,
            state=state,
            provider=self.key,
            raw=data,
        )
