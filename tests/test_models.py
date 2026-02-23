"""Tests for pydantic models."""
from decimal import Decimal

import pytest

from merchants.models import PaymentState, PaymentStatus, WebhookEvent


class TestPaymentStatus:
    def test_is_final_succeeded(self):
        s = PaymentStatus(payment_id="p1", state=PaymentState.SUCCEEDED, provider="test")
        assert s.is_final is True
        assert s.is_success is True

    def test_is_final_failed(self):
        s = PaymentStatus(payment_id="p1", state=PaymentState.FAILED, provider="test")
        assert s.is_final is True
        assert s.is_success is False

    def test_is_final_cancelled(self):
        s = PaymentStatus(payment_id="p1", state=PaymentState.CANCELLED, provider="test")
        assert s.is_final is True

    def test_is_final_refunded(self):
        s = PaymentStatus(payment_id="p1", state=PaymentState.REFUNDED, provider="test")
        assert s.is_final is True

    def test_not_final_pending(self):
        s = PaymentStatus(payment_id="p1", state=PaymentState.PENDING, provider="test")
        assert s.is_final is False
        assert s.is_success is False

    def test_not_final_processing(self):
        s = PaymentStatus(payment_id="p1", state=PaymentState.PROCESSING, provider="test")
        assert s.is_final is False

    def test_not_final_unknown(self):
        s = PaymentStatus(payment_id="p1", state=PaymentState.UNKNOWN, provider="test")
        assert s.is_final is False

    def test_with_amount(self):
        s = PaymentStatus(
            payment_id="p1",
            state=PaymentState.SUCCEEDED,
            provider="test",
            amount=Decimal("19.99"),
            currency="USD",
        )
        assert s.amount == Decimal("19.99")
        assert s.currency == "USD"


class TestWebhookEvent:
    def test_defaults(self):
        e = WebhookEvent(event_type="payment.success")
        assert e.state == PaymentState.UNKNOWN
        assert e.provider == "unknown"
        assert e.event_id is None
        assert e.payment_id is None
