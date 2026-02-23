"""Webhook verification and parsing utilities."""
from __future__ import annotations

import hashlib
import hmac
import json
from typing import Any

from merchants.models import PaymentState, WebhookEvent
from merchants.providers import normalise_state


class WebhookVerificationError(Exception):
    """Raised when webhook HMAC signature verification fails."""


def verify_signature(
    payload: bytes,
    secret: str | bytes,
    signature: str,
    *,
    header_prefix: str = "sha256=",
) -> None:
    """Verify an HMAC-SHA256 webhook signature using constant-time comparison.

    Args:
        payload: Raw request body bytes.
        secret: Webhook signing secret (str or bytes).
        signature: The value from the provider's signature header
            (e.g. ``"sha256=abc123…"``).
        header_prefix: Expected prefix on the signature value
            (default: ``"sha256="``).

    Raises:
        WebhookVerificationError: If the signature does not match.
    """
    if isinstance(secret, str):
        secret = secret.encode()

    expected_hex = hmac.new(secret, payload, hashlib.sha256).hexdigest()

    # Strip optional prefix from provided signature
    provided = signature
    if provided.startswith(header_prefix):
        provided = provided[len(header_prefix):]

    if not hmac.compare_digest(expected_hex, provided):
        raise WebhookVerificationError("Webhook signature verification failed.")


def parse_event(
    payload: bytes,
    *,
    provider: str = "unknown",
) -> WebhookEvent:
    """Best-effort parse and normalisation of a raw webhook payload.

    Tries to extract common fields (``id``, ``event_type``/``type``,
    ``payment_id``, ``status``) regardless of provider format.

    Args:
        payload: Raw request body bytes.
        provider: Provider name hint for the returned event.

    Returns:
        A :class:`~merchants.models.WebhookEvent`.  Fields that cannot be
        extracted are left as ``None`` / ``PaymentState.UNKNOWN``.
    """
    try:
        data: dict[str, Any] = json.loads(payload)
    except (ValueError, TypeError):
        data = {}

    event_id = data.get("id") or data.get("event_id")
    event_type = str(data.get("type") or data.get("event_type") or "unknown")
    payment_id = (
        data.get("payment_id")
        or data.get("resource", {}).get("id")
        or data.get("data", {}).get("object", {}).get("id")
    )

    # Try to extract a raw status from common structures
    raw_status: str = (
        data.get("status")
        or data.get("data", {}).get("object", {}).get("status")
        or data.get("resource", {}).get("status")
        or "unknown"
    )
    state: PaymentState = normalise_state(str(raw_status))

    return WebhookEvent(
        event_id=event_id,
        event_type=event_type,
        payment_id=payment_id,
        state=state,
        provider=provider,
        raw=data,
    )
