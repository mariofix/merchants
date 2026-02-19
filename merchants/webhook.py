"""Webhook helpers: HMAC-SHA256 verification and event parsing."""

from __future__ import annotations

import hashlib
import hmac
import json
from typing import Any

from merchants.errors import ParseError, WebhookVerificationError
from merchants.payments import PaymentState
from merchants.result import Failure, Success


class WebhookEvent:
    """Parsed webhook event with best-effort field extraction."""

    def __init__(
        self,
        event_type: str,
        payment_id: str | None,
        state: PaymentState | None,
        failure_reason: str | None,
        raw: dict[str, Any],
    ) -> None:
        self.event_type = event_type
        self.payment_id = payment_id
        self.state = state
        self.failure_reason = failure_reason
        self.raw = raw

    def __repr__(self) -> str:
        return (
            f"WebhookEvent(event_type={self.event_type!r}, "
            f"payment_id={self.payment_id!r}, state={self.state!r})"
        )


def verify_signature(
    payload: bytes,
    signature: str,
    secret: str,
    *,
    digest: str = "sha256",
) -> None:
    """Verify an HMAC signature using constant-time comparison.

    Parameters
    ----------
    payload:
        Raw request body bytes.
    signature:
        The signature value extracted from the request header.
    secret:
        Shared HMAC secret.
    digest:
        Hash algorithm name accepted by :mod:`hashlib` (default ``"sha256"``).
        Pass only trusted, known algorithm names (e.g. ``"sha256"``, ``"sha512"``).

    Raises
    ------
    WebhookVerificationError
        When the computed HMAC does not match *signature*.
    """
    expected = hmac.new(secret.encode(), payload, digestmod=digest).hexdigest()
    if not hmac.compare_digest(expected, signature):
        raise WebhookVerificationError("Webhook signature verification failed.")


def parse_event(payload: bytes) -> "Success[WebhookEvent] | Failure[ParseError]":
    """Parse a raw webhook payload into a :class:`WebhookEvent`.

    Performs best-effort field extraction; unknown fields are tolerated.

    Returns
    -------
    Success[WebhookEvent]
        When the payload is valid JSON.
    Failure[ParseError]
        When the payload cannot be decoded or is not a JSON object.
    """
    try:
        data: dict[str, Any] = json.loads(payload)
    except (json.JSONDecodeError, ValueError) as exc:
        return Failure(ParseError(f"Invalid JSON payload: {exc}"))

    if not isinstance(data, dict):
        return Failure(ParseError("Webhook payload must be a JSON object."))

    event_type: str = "unknown"
    for key in ("event_type", "type"):
        val = data.get(key)
        if val is not None:
            event_type = val
            break

    payment_id: str | None = None
    for key in ("payment_id", "id"):
        val = data.get(key)
        if val is not None:
            payment_id = val
            break
    if payment_id is None:
        nested = data.get("data")
        if isinstance(nested, dict):
            payment_id = nested.get("id")
    raw_state: str | None = data.get("state") or data.get("status")
    state: PaymentState | None = None
    if raw_state is not None:
        try:
            state = PaymentState(raw_state.upper())
        except ValueError:
            state = PaymentState.UNKNOWN

    failure_reason: str | None = data.get("failure_reason") or data.get("error")

    return Success(
        WebhookEvent(
            event_type=event_type,
            payment_id=payment_id,
            state=state,
            failure_reason=failure_reason,
            raw=data,
        )
    )
