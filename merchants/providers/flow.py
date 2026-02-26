"""Flow.cl provider – wraps the ``pyflowcl`` package."""

from __future__ import annotations

import json
from decimal import Decimal
from typing import Any

from merchants.amount import to_minor_units
from merchants.models import CheckoutSession, PaymentState, PaymentStatus, WebhookEvent
from merchants.providers import Provider, UserError

try:
    from pyflowcl.Clients import ApiClient
    from pyflowcl.exceptions import GenericError
    from pyflowcl.Payment import create as flow_create
    from pyflowcl.Payment import getStatus as flow_get_status
except ImportError as exc:  # pragma: no cover
    raise ImportError("pyflowcl is required for FlowProvider. Install it with: pip install pyflowcl") from exc

# Flow status codes: 1=Paid, 2=Rejected, 3=Pending, 4=Cancelled
_FLOW_STATE_MAP: dict[int, PaymentState] = {
    1: PaymentState.SUCCEEDED,
    2: PaymentState.FAILED,
    3: PaymentState.PENDING,
    4: PaymentState.CANCELLED,
}


class FlowProvider(Provider):
    """Flow.cl payment provider.

    Uses the ``pyflowcl`` package to create and query payments on
    `Flow.cl <https://www.flow.cl>`_.

    Args:
        api_key: Flow API key.
        api_secret: Flow API secret (used for HMAC-SHA256 request signing).
        api_url: Override the base URL (default: ``"https://www.flow.cl/api"``).
        subject: Default payment subject / description.
        confirmation_url: URL Flow calls after payment is processed.
    """

    key = "flow"
    name = "Flow.cl"
    author = "merchants team"
    version = "1.0.0"
    description = "Flow.cl payment gateway for Chile, powered by pyflowcl."
    url = "https://www.flow.cl"

    def __init__(
        self,
        api_key: str,
        api_secret: str,
        *,
        api_url: str = "https://www.flow.cl/api",
        subject: str = "Order",
        confirmation_url: str = "",
    ) -> None:
        self._client = ApiClient(
            api_url=api_url,
            api_key=api_key,
            api_secret=api_secret,
        )
        self._subject = subject
        self._confirmation_url = confirmation_url

    def create_checkout(
        self,
        amount: Decimal,
        currency: str,
        success_url: str,
        cancel_url: str,
        metadata: dict[str, Any] | None = None,
    ) -> CheckoutSession:
        # Flow expects integer amounts in CLP
        amount_int = to_minor_units(amount, decimals=0)
        payment_data: dict[str, Any] = {
            "amount": amount_int,
            "commerceOrder": (metadata or {}).get("order_id", ""),
            "currency": currency.upper(),
            "subject": self._subject,
            "urlReturn": success_url,
            "urlConfirmation": self._confirmation_url or success_url,
        }
        try:
            response = flow_create(self._client, payment_data)
        except GenericError as exc:
            raise UserError(str(exc)) from exc

        redirect_url = f"{response.url}?token={response.token}" if response.url and response.token else ""
        return CheckoutSession(
            session_id=str(response.token or ""),
            redirect_url=redirect_url,
            provider=self.key,
            amount=amount,
            currency=currency,
            metadata=metadata or {},
            raw={"token": response.token, "flowOrder": response.flowOrder},
        )

    def get_payment(self, payment_id: str) -> PaymentStatus:
        try:
            status = flow_get_status(self._client, payment_id)
        except GenericError as exc:
            raise UserError(str(exc)) from exc

        state = _FLOW_STATE_MAP.get(status.status or 0, PaymentState.UNKNOWN)
        return PaymentStatus(
            payment_id=payment_id,
            state=state,
            provider=self.key,
            amount=Decimal(str(status.amount)) if status.amount is not None else None,
            currency=status.currency,
            raw={
                "status": status.status,
                "commerceOrder": status.commerceOrder,
                "payer": status.payer,
            },
        )

    def parse_webhook(self, payload: bytes, headers: dict[str, str]) -> WebhookEvent:
        # Flow sends a form POST with a `token` field; payload may be form-encoded
        token = ""
        try:
            data: dict[str, Any] = json.loads(payload)
            token = data.get("token", "")
        except ValueError:
            # form-encoded: token=xxx
            from urllib.parse import parse_qs

            qs = parse_qs(payload.decode(errors="replace"))
            token = (qs.get("token") or [""])[0]
            data = {"token": token}

        return WebhookEvent(
            event_id=token or None,
            event_type="payment.notification",
            payment_id=token or None,
            state=PaymentState.UNKNOWN,  # must call get_payment(token) to know state
            provider=self.key,
            raw=data,
        )
