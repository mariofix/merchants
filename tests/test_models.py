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
            merchants_id="550e8400-e29b-41d4-a716-446655440000",
            amount=Decimal("9.99"),
            currency="USD",
            provider="stripe",
        )
        assert p.merchants_id == "550e8400-e29b-41d4-a716-446655440000"
        assert p.amount == Decimal("9.99")
        assert p.currency == "USD"
        assert p.provider == "stripe"

    def test_defaults(self):
        p = PaymentModel(
            merchants_id="550e8400-e29b-41d4-a716-446655440000",
            amount=Decimal("1.00"),
            currency="EUR",
            provider="dummy",
        )
        assert p.state == PaymentState.PENDING
        assert p.transaction_id is None
        assert p.cancel_url is None
        assert p.success_url is None
        assert p.email is None
        assert p.extra_args == {}
        assert p.request_payload == {}
        assert p.response_payload == {}
        assert p.payment_object == {}

    def test_full_construction(self):
        p = PaymentModel(
            merchants_id="550e8400-e29b-41d4-a716-446655440000",
            transaction_id="sess_abc123",
            amount=Decimal("49.99"),
            currency="USD",
            provider="stripe",
            state=PaymentState.PROCESSING,
            success_url="https://example.com/success",
            cancel_url="https://example.com/cancel",
            email="user@example.com",
            extra_args={"timeout": 30},
            request_payload={"product_id": "prod_001"},
            response_payload={"redirect_url": "https://checkout.stripe.com/..."},
            payment_object={"id": "pi_abc", "status": "processing"},
        )
        assert p.transaction_id == "sess_abc123"
        assert p.state == PaymentState.PROCESSING
        assert p.cancel_url == "https://example.com/cancel"
        assert p.success_url == "https://example.com/success"
        assert p.email == "user@example.com"
        assert p.extra_args == {"timeout": 30}
        assert p.request_payload == {"product_id": "prod_001"}
        assert p.response_payload == {"redirect_url": "https://checkout.stripe.com/..."}
        assert p.payment_object == {"id": "pi_abc", "status": "processing"}

    def test_state_validates_enum_values(self):
        p = PaymentModel(
            merchants_id="550e8400-e29b-41d4-a716-446655440000",
            amount=Decimal("5.00"),
            currency="USD",
            provider="dummy",
            state=PaymentState.SUCCEEDED,
        )
        assert p.state == PaymentState.SUCCEEDED
