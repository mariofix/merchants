"""Unit tests for the merchants SDK MVP.

Covers:
- amount conversion (decimal string default and minor unit conversion)
- webhook HMAC verification
- provider registry selection
- payment state normalization
"""

from __future__ import annotations

import hashlib
import hmac
import json
from decimal import Decimal

import pytest

from merchants.amount import to_decimal_string, to_minor_units
from merchants.client import MerchantsClient
from merchants.errors import (
    ParseError,
    ProviderNotFoundError,
    WebhookVerificationError,
)
from merchants.payments import PaymentState, PaymentStatus
from merchants.providers import ProviderRegistry
from merchants.providers.mock import MockProvider
from merchants.providers.paypal import PayPalProvider
from merchants.providers.stripe import StripeProvider
from merchants.result import Failure, Success
from merchants.webhook import WebhookEvent, parse_event, verify_signature


# ---------------------------------------------------------------------------
# Amount helpers
# ---------------------------------------------------------------------------


class TestToDecimalString:
    def test_basic(self):
        assert to_decimal_string(Decimal("19.99")) == "19.99"

    def test_whole_number(self):
        assert to_decimal_string(Decimal("100")) == "100"

    def test_many_decimals(self):
        assert to_decimal_string(Decimal("0.001")) == "0.001"

    def test_zero(self):
        assert to_decimal_string(Decimal("0")) == "0"


class TestToMinorUnits:
    def test_two_decimal_places(self):
        assert to_minor_units(Decimal("19.99")) == 1999

    def test_whole_amount(self):
        assert to_minor_units(Decimal("100")) == 10000

    def test_zero_decimal_currency(self):
        # e.g. JPY
        assert to_minor_units(Decimal("500"), exponent=0) == 500

    def test_three_decimal_places(self):
        # e.g. KWD (3 decimal places)
        assert to_minor_units(Decimal("1.234"), exponent=3) == 1234

    def test_rounding(self):
        # 19.995 rounds to 2000 cents
        assert to_minor_units(Decimal("19.995"), exponent=2) == 2000

    def test_zero(self):
        assert to_minor_units(Decimal("0"), exponent=2) == 0


# ---------------------------------------------------------------------------
# Webhook HMAC verification
# ---------------------------------------------------------------------------


def _make_signature(payload: bytes, secret: str) -> str:
    return hmac.new(secret.encode(), payload, digestmod=hashlib.sha256).hexdigest()


class TestVerifySignature:
    def test_valid_signature(self):
        payload = b'{"event_type":"payment.succeeded"}'
        secret = "mysecret"
        sig = _make_signature(payload, secret)
        # Should not raise
        verify_signature(payload, sig, secret)

    def test_invalid_signature_raises(self):
        payload = b'{"event_type":"payment.succeeded"}'
        with pytest.raises(WebhookVerificationError):
            verify_signature(payload, "badsignature", "mysecret")

    def test_empty_payload(self):
        payload = b""
        secret = "s3cr3t"
        sig = _make_signature(payload, secret)
        verify_signature(payload, sig, secret)

    def test_wrong_secret_raises(self):
        payload = b"hello"
        sig = _make_signature(payload, "correct_secret")
        with pytest.raises(WebhookVerificationError):
            verify_signature(payload, sig, "wrong_secret")


# ---------------------------------------------------------------------------
# Webhook event parsing
# ---------------------------------------------------------------------------


class TestParseEvent:
    def test_parse_succeeded_event(self):
        data = {
            "event_type": "payment.succeeded",
            "payment_id": "pay_123",
            "state": "SUCCEEDED",
        }
        result = parse_event(json.dumps(data).encode())
        assert isinstance(result, Success)
        event = result.value
        assert event.event_type == "payment.succeeded"
        assert event.payment_id == "pay_123"
        assert event.state == PaymentState.SUCCEEDED

    def test_parse_failed_event_with_reason(self):
        data = {
            "event_type": "payment.failed",
            "payment_id": "pay_456",
            "state": "FAILED",
            "failure_reason": "insufficient_funds",
        }
        result = parse_event(json.dumps(data).encode())
        assert isinstance(result, Success)
        event = result.value
        assert event.state == PaymentState.FAILED
        assert event.failure_reason == "insufficient_funds"

    def test_parse_invalid_json_returns_failure(self):
        result = parse_event(b"not valid json")
        assert isinstance(result, Failure)
        assert isinstance(result.error, ParseError)

    def test_parse_non_object_json_returns_failure(self):
        result = parse_event(b'["a", "b"]')
        assert isinstance(result, Failure)

    def test_parse_unknown_state(self):
        data = {"event_type": "payment.whatever", "state": "SOME_WEIRD_STATE"}
        result = parse_event(json.dumps(data).encode())
        assert isinstance(result, Success)
        assert result.value.state == PaymentState.UNKNOWN

    def test_parse_missing_fields_uses_defaults(self):
        data = {"type": "ping"}
        result = parse_event(json.dumps(data).encode())
        assert isinstance(result, Success)
        event = result.value
        assert event.event_type == "ping"
        assert event.payment_id is None
        assert event.state is None


# ---------------------------------------------------------------------------
# Provider registry
# ---------------------------------------------------------------------------


class TestProviderRegistry:
    def test_register_and_get(self):
        reg = ProviderRegistry()
        mock = MockProvider()
        reg.register("mock", mock)
        assert reg.get("mock") is mock

    def test_get_unknown_raises(self):
        reg = ProviderRegistry()
        with pytest.raises(ProviderNotFoundError) as exc_info:
            reg.get("nonexistent")
        assert "nonexistent" in str(exc_info.value)

    def test_names(self):
        reg = ProviderRegistry()
        reg.register("a", MockProvider())
        reg.register("b", MockProvider())
        assert set(reg.names()) == {"a", "b"}

    def test_overwrite_registration(self):
        reg = ProviderRegistry()
        p1 = MockProvider()
        p2 = MockProvider()
        reg.register("p", p1)
        reg.register("p", p2)
        assert reg.get("p") is p2


# ---------------------------------------------------------------------------
# MerchantsClient with provider selection
# ---------------------------------------------------------------------------


class TestMerchantsClientProviderSelection:
    def test_select_provider_by_name(self):
        reg = ProviderRegistry()
        reg.register("mock", MockProvider())
        client = MerchantsClient(provider="mock", registry=reg)
        assert isinstance(client.provider, MockProvider)

    def test_select_provider_by_instance(self):
        provider = MockProvider()
        client = MerchantsClient(provider=provider)
        assert client.provider is provider

    def test_unknown_provider_name_raises(self):
        reg = ProviderRegistry()
        with pytest.raises(ProviderNotFoundError):
            MerchantsClient(provider="stripe", registry=reg)

    def test_create_checkout_with_mock(self):
        client = MerchantsClient(provider=MockProvider())
        session = client.create_checkout(
            Decimal("49.99"),
            "USD",
            return_url="https://example.com/return",
        )
        assert session.id.startswith("mock_")
        assert session.redirect_url.startswith("https://mock.example.com/pay/")

    def test_get_payment_with_mock(self):
        mock = MockProvider()
        client = MerchantsClient(provider=mock)
        session = client.create_checkout(
            Decimal("10.00"),
            "EUR",
            return_url="https://example.com/return",
        )
        status = client.get_payment(session.id)
        assert status.id == session.id
        assert status.state == PaymentState.SUCCEEDED


# ---------------------------------------------------------------------------
# PaymentStatus model
# ---------------------------------------------------------------------------


class TestPaymentStatusModel:
    def test_is_final_succeeded(self):
        s = PaymentStatus(id="1", state=PaymentState.SUCCEEDED)
        assert s.is_final is True
        assert s.is_success is True

    def test_is_final_failed(self):
        s = PaymentStatus(id="1", state=PaymentState.FAILED)
        assert s.is_final is True
        assert s.is_success is False

    def test_is_final_canceled(self):
        s = PaymentStatus(id="1", state=PaymentState.CANCELED)
        assert s.is_final is True

    def test_not_final_pending(self):
        s = PaymentStatus(id="1", state=PaymentState.PENDING)
        assert s.is_final is False
        assert s.is_success is False

    def test_not_final_unknown(self):
        s = PaymentStatus(id="1", state=PaymentState.UNKNOWN)
        assert s.is_final is False


# ---------------------------------------------------------------------------
# Provider state normalization
# ---------------------------------------------------------------------------


class TestStripeStateNormalization:
    @pytest.mark.parametrize(
        "stripe_status, expected",
        [
            ("succeeded", PaymentState.SUCCEEDED),
            ("canceled", PaymentState.CANCELED),
            ("processing", PaymentState.PENDING),
            ("requires_payment_method", PaymentState.PENDING),
            ("unknown_future_status", PaymentState.UNKNOWN),
        ],
    )
    def test_normalize(self, stripe_status, expected):
        assert StripeProvider.normalize_state(stripe_status) == expected


class TestPayPalStateNormalization:
    @pytest.mark.parametrize(
        "paypal_status, expected",
        [
            ("COMPLETED", PaymentState.SUCCEEDED),
            ("VOIDED", PaymentState.CANCELED),
            ("CREATED", PaymentState.PENDING),
            ("APPROVED", PaymentState.PENDING),
            ("SOMETHING_ELSE", PaymentState.UNKNOWN),
        ],
    )
    def test_normalize(self, paypal_status, expected):
        assert PayPalProvider.normalize_state(paypal_status) == expected


# ---------------------------------------------------------------------------
# Result types
# ---------------------------------------------------------------------------


class TestResultTypes:
    def test_success_ok(self):
        r = Success("hello")
        assert r.ok is True
        assert r.value == "hello"

    def test_failure_ok(self):
        err = ParseError("bad")
        r = Failure(err)
        assert r.ok is False
        assert r.error is err
