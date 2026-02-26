"""Tests for webhook verification and parsing."""

import hashlib
import hmac
import json

import pytest

from merchants.models import PaymentState
from merchants.webhooks import WebhookVerificationError, parse_event, verify_signature


def _make_sig(payload: bytes, secret: str, prefix: str = "sha256=") -> str:
    digest = hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()
    return f"{prefix}{digest}"


class TestVerifySignature:
    def test_valid_signature(self):
        payload = b'{"id":"evt_1","type":"payment.succeeded"}'
        secret = "whsec_test"
        sig = _make_sig(payload, secret)
        # Should not raise
        verify_signature(payload, secret, sig)

    def test_invalid_signature_raises(self):
        payload = b'{"id":"evt_1"}'
        with pytest.raises(WebhookVerificationError):
            verify_signature(payload, "secret", "sha256=badhex")

    def test_bytes_secret(self):
        payload = b"hello"
        secret = b"s3cr3t"
        digest = hmac.new(secret, payload, hashlib.sha256).hexdigest()
        verify_signature(payload, secret, f"sha256={digest}")

    def test_signature_without_prefix(self):
        payload = b"data"
        secret = "mykey"
        digest = hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()
        verify_signature(payload, secret, digest, header_prefix="")

    def test_tampered_payload_raises(self):
        payload = b'{"amount":"100"}'
        secret = "key"
        sig = _make_sig(payload, secret)
        with pytest.raises(WebhookVerificationError):
            verify_signature(b'{"amount":"999"}', secret, sig)


class TestParseEvent:
    def test_stripe_style(self):
        data = {
            "id": "evt_stripe_1",
            "type": "payment_intent.succeeded",
            "data": {"object": {"id": "pi_123", "status": "succeeded"}},
        }
        event = parse_event(json.dumps(data).encode(), provider="stripe")
        assert event.event_id == "evt_stripe_1"
        assert event.event_type == "payment_intent.succeeded"
        assert event.payment_id == "pi_123"
        assert event.state == PaymentState.SUCCEEDED
        assert event.provider == "stripe"

    def test_paypal_style(self):
        data = {
            "id": "WH-123",
            "event_type": "PAYMENT.CAPTURE.COMPLETED",
            "resource": {"id": "order_abc", "status": "completed"},
        }
        event = parse_event(json.dumps(data).encode(), provider="paypal")
        assert event.event_id == "WH-123"
        assert event.event_type == "PAYMENT.CAPTURE.COMPLETED"
        assert event.payment_id == "order_abc"
        assert event.state == PaymentState.SUCCEEDED

    def test_generic_style(self):
        data = {
            "event_id": "ev_1",
            "event_type": "payment.failed",
            "payment_id": "pay_999",
            "status": "failed",
        }
        event = parse_event(json.dumps(data).encode())
        assert event.state == PaymentState.FAILED
        assert event.payment_id == "pay_999"

    def test_invalid_json(self):
        event = parse_event(b"not json")
        assert event.event_type == "unknown"
        assert event.state == PaymentState.UNKNOWN

    def test_unknown_status(self):
        data = {"type": "payment.mystery", "status": "foobar"}
        event = parse_event(json.dumps(data).encode())
        assert event.state == PaymentState.UNKNOWN
