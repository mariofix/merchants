"""Khipu provider - wraps the ``khipu-tools`` package."""
from __future__ import annotations

import json
import logging
from decimal import Decimal
from typing import Any

logger = logging.getLogger(__name__)

from merchants.amount import to_decimal_string
from merchants.auth import ApiKeyAuth
from merchants.models import CheckoutSession, PaymentState, PaymentStatus, WebhookEvent
from merchants.providers import Provider, UserError
from merchants.webhooks import WebhookVerificationError, verify_khipu_signature

try:
    import khipu_tools
except ImportError as exc:  # pragma: no cover
    raise ImportError(
        "khipu-tools is required for KhipuProvider. Install it with: pip install khipu-tools"
    ) from exc

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
    accepts_notify_url = True

    def __init__(
        self,
        api_key: str,
        *,
        key: str | None = None,
        name: str | None = None,
        description: str | None = None,
        subject: str = "Order",
        notify_url: str = "",
        webhook_secret: str = "",
    ) -> None:
        logger.debug("khipu.py: KhipuProvider.__init__ called")
        super().__init__(key=key, name=name, description=description)
        self._api_key = api_key
        # khipu_tools uses a Stripe-style global api_key. This is safe for
        # single-provider deployments; if multiple KhipuProvider instances with
        # different keys are ever needed, use per-request KhipuClient instances.
        khipu_tools.api_key = api_key
        self._base_url = khipu_tools.DEFAULT_API_BASE
        self._auth = ApiKeyAuth(api_key, header="x-api-key")
        self._subject = subject
        self._notify_url = notify_url
        self._webhook_secret = webhook_secret

    def create_checkout(
        self,
        amount: Decimal,
        currency: str,
        success_url: str,
        cancel_url: str,
        metadata: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> CheckoutSession:
        logger.debug(
            "khipu.py: KhipuProvider.create_checkout called with amount=%s currency=%s",
            amount, currency,
        )
        params: dict[str, Any] = {
            "amount": to_decimal_string(amount),
            "currency": currency.upper(),
            "subject": self._subject,
            "return_url": success_url,
            "cancel_url": cancel_url,
            "notify_api_version": "3.0",
        }
        # notify_url is a provider concern — comes via extra_args (kwargs),
        # falling back to the instance default.
        notify_url = kwargs.get("notify_url") or self._notify_url
        if notify_url:
            params["notify_url"] = notify_url
        if metadata and metadata.get("order_id"):
            params["transaction_id"] = str(metadata["order_id"])
        body = kwargs.get("body", "")
        if body:
            params["body"] = body

        logger.debug("khipu.py: KhipuProvider.create_checkout params=%r", params)
        try:
            result = khipu_tools.Payments.create(**params)
        except Exception as exc:
            raise UserError(str(exc)) from exc

        logger.debug("khipu.py: KhipuProvider.create_checkout result=%r", result)
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
        logger.debug("khipu.py: KhipuProvider.get_payment called with payment_id=%s", payment_id)
        try:
            result = khipu_tools.Payments.get(payment_id=payment_id)
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
        """Parse a Khipu v3.0 webhook notification.

        The v3.0 API sends a JSON body with full payment data and an
        ``x-khipu-signature`` header for HMAC-SHA256 verification.  When
        ``webhook_secret`` is configured, the signature is verified before
        the event is returned.

        The payment state is determined by the presence of
        ``conciliation_date`` in the body (→ SUCCEEDED).

        Args:
            payload: Raw request body bytes.
            headers: Request headers dict.

        Returns:
            A :class:`WebhookEvent` with the parsed data.

        Raises:
            WebhookVerificationError: If signature verification is enabled
                and fails.
        """
        logger.debug("khipu.py: KhipuProvider.parse_webhook called")

        # Verify signature when a webhook secret is configured
        sig_header = headers.get("X-Khipu-Signature") or headers.get("x-khipu-signature", "")
        if self._webhook_secret and sig_header:
            verify_khipu_signature(payload, self._webhook_secret, sig_header)
        elif self._webhook_secret and not sig_header:
            raise WebhookVerificationError(
                "Webhook secret is configured but x-khipu-signature header is missing."
            )

        try:
            data: dict[str, Any] = json.loads(payload)
        except ValueError:
            from urllib.parse import parse_qs
            qs = parse_qs(payload.decode(errors="replace"))
            data = {k: v[0] for k, v in qs.items()}

        payment_id = data.get("payment_id")

        # v3.0: determine state from conciliation_date presence
        # If conciliation_date is present and non-empty, the payment is reconciled (succeeded).
        # Otherwise fall back to payment_status for backward compatibility.
        if data.get("conciliation_date"):
            state = PaymentState.SUCCEEDED
            event_type = "payment.conciliated"
        elif "payment_status" in data:
            raw_state = str(data["payment_status"])
            state = _KHIPU_STATE_MAP.get(raw_state.lower(), PaymentState.UNKNOWN)
            event_type = "payment.notification"
        else:
            state = PaymentState.UNKNOWN
            event_type = "payment.notification"

        return WebhookEvent(
            event_id=payment_id,
            event_type=event_type,
            payment_id=payment_id,
            state=state,
            provider=self.key,
            raw=data,
        )
