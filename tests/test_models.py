"""Tests for pydantic models."""

from decimal import Decimal

from merchants.models import PaymentModel, PaymentState, PaymentStatus, WebhookEvent


class TestPaymentStatus:
    def test_is_final_succeeded(self):
        s = PaymentStatus(
            payment_id="p1", state=PaymentState.SUCCEEDED, provider="test"
        )
        assert s.is_final is True
        assert s.is_success is True

    def test_is_final_failed(self):
        s = PaymentStatus(payment_id="p1", state=PaymentState.FAILED, provider="test")
        assert s.is_final is True
        assert s.is_success is False

    def test_is_final_cancelled(self):
        s = PaymentStatus(
            payment_id="p1", state=PaymentState.CANCELLED, provider="test"
        )
        assert s.is_final is True

    def test_is_final_refunded(self):
        s = PaymentStatus(payment_id="p1", state=PaymentState.REFUNDED, provider="test")
        assert s.is_final is True

    def test_not_final_pending(self):
        s = PaymentStatus(payment_id="p1", state=PaymentState.PENDING, provider="test")
        assert s.is_final is False
        assert s.is_success is False

    def test_not_final_processing(self):
        s = PaymentStatus(
            payment_id="p1", state=PaymentState.PROCESSING, provider="test"
        )
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


class TestPaymentModel:
    def test_minimal_construction(self):
        p = PaymentModel(
            amount=Decimal("9.99"),
            currency="USD",
            provider="stripe",
            success_url="https://example.com/success",
        )
        assert p.amount == Decimal("9.99")
        assert p.currency == "USD"
        assert p.provider == "stripe"
        assert p.success_url == "https://example.com/success"

    def test_defaults(self):
        p = PaymentModel(
            amount=Decimal("1.00"),
            currency="EUR",
            provider="dummy",
            success_url="https://example.com/ok",
        )
        assert p.state == PaymentState.PENDING
        assert p.payment_id is None
        assert p.cancel_url is None
        assert p.email is None
        assert p.request_context == {}
        assert p.response_payload == {}

    def test_full_construction(self):
        p = PaymentModel(
            payment_id="sess_abc123",
            amount=Decimal("49.99"),
            currency="USD",
            provider="stripe",
            state=PaymentState.PROCESSING,
            success_url="https://example.com/success",
            cancel_url="https://example.com/cancel",
            email="user@example.com",
            request_context={"product_id": "prod_001"},
            response_payload={"redirect_url": "https://checkout.stripe.com/..."},
        )
        assert p.payment_id == "sess_abc123"
        assert p.state == PaymentState.PROCESSING
        assert p.cancel_url == "https://example.com/cancel"
        assert p.email == "user@example.com"
        assert p.request_context == {"product_id": "prod_001"}
        assert p.response_payload == {"redirect_url": "https://checkout.stripe.com/..."}

    def test_state_validates_enum_values(self):
        p = PaymentModel(
            amount=Decimal("5.00"),
            currency="USD",
            provider="dummy",
            success_url="https://example.com/ok",
            state=PaymentState.SUCCEEDED,
        )
        assert p.state == PaymentState.SUCCEEDED
