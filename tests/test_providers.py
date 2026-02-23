"""Tests for provider selection, registry, and state normalisation."""
from decimal import Decimal
from unittest.mock import MagicMock

import pytest

from merchants.models import PaymentState
from merchants.providers import (
    Provider,
    UserError,
    get_provider,
    list_providers,
    normalise_state,
    register_provider,
)
from merchants.providers.generic import GenericProvider
from merchants.providers.paypal import PayPalProvider
from merchants.providers.stripe import StripeProvider
from merchants.transport import HttpResponse


class TestNormaliseState:
    @pytest.mark.parametrize(
        "raw, expected",
        [
            ("succeeded", PaymentState.SUCCEEDED),
            ("SUCCEEDED", PaymentState.SUCCEEDED),
            ("failed", PaymentState.FAILED),
            ("canceled", PaymentState.CANCELLED),
            ("cancelled", PaymentState.CANCELLED),
            ("processing", PaymentState.PROCESSING),
            ("pending", PaymentState.PENDING),
            ("created", PaymentState.PENDING),
            ("approved", PaymentState.PROCESSING),
            ("completed", PaymentState.SUCCEEDED),
            ("voided", PaymentState.CANCELLED),
            ("refunded", PaymentState.REFUNDED),
            ("paid", PaymentState.SUCCEEDED),
            ("success", PaymentState.SUCCEEDED),
            ("error", PaymentState.FAILED),
            ("xyzzy", PaymentState.UNKNOWN),
        ],
    )
    def test_mapping(self, raw, expected):
        assert normalise_state(raw) == expected


class TestProviderRegistry:
    def setup_method(self):
        self._dummy = _make_dummy_provider("test_dummy")
        register_provider(self._dummy)

    def test_get_by_key(self):
        p = get_provider("test_dummy")
        assert p is self._dummy

    def test_get_by_instance(self):
        p = get_provider(self._dummy)
        assert p is self._dummy

    def test_unknown_key_raises(self):
        with pytest.raises(KeyError, match="not_a_real_provider"):
            get_provider("not_a_real_provider")

    def test_list_providers_includes_registered(self):
        assert "test_dummy" in list_providers()


class TestStripeProvider:
    def _make_transport(self, status_code: int, body: dict) -> MagicMock:
        t = MagicMock()
        t.send.return_value = HttpResponse(status_code, {}, body)
        return t

    def test_create_checkout_success(self):
        body = {"id": "cs_test_123", "url": "https://stripe.com/pay/cs_test_123"}
        transport = self._make_transport(200, body)
        provider = StripeProvider("sk_test_key", transport=transport)
        session = provider.create_checkout(
            Decimal("19.99"), "USD",
            "https://example.com/ok", "https://example.com/cancel",
        )
        assert session.redirect_url == "https://stripe.com/pay/cs_test_123"
        assert session.provider == "stripe"
        # Verify minor-units were sent
        payload = transport.send.call_args.kwargs["json"]
        assert payload["line_items"][0]["price_data"]["unit_amount"] == 1999

    def test_create_checkout_failure(self):
        body = {"error": {"message": "Invalid API key"}}
        transport = self._make_transport(401, body)
        provider = StripeProvider("bad_key", transport=transport)
        with pytest.raises(UserError):
            provider.create_checkout(
                Decimal("9.99"), "USD",
                "https://example.com/ok", "https://example.com/cancel",
            )

    def test_zero_decimal_currency(self):
        """JPY should use 0 decimal places (amount in yen, not sen)."""
        body = {"id": "cs_jpy", "url": "https://stripe.com/pay/cs_jpy"}
        transport = self._make_transport(200, body)
        provider = StripeProvider("sk_test_key", transport=transport)
        provider.create_checkout(
            Decimal("1000"), "JPY",
            "https://example.com/ok", "https://example.com/cancel",
        )
        payload = transport.send.call_args.kwargs["json"]
        assert payload["line_items"][0]["price_data"]["unit_amount"] == 1000


class TestPayPalProvider:
    def _make_transport(self, status_code: int, body: dict) -> MagicMock:
        t = MagicMock()
        t.send.return_value = HttpResponse(status_code, {}, body)
        return t

    def test_create_checkout_success(self):
        body = {
            "id": "ORDER-123",
            "links": [
                {"rel": "self", "href": "https://paypal.com/self"},
                {"rel": "approve", "href": "https://paypal.com/approve/ORDER-123"},
            ],
        }
        transport = self._make_transport(201, body)
        provider = PayPalProvider("token_xyz", transport=transport)
        session = provider.create_checkout(
            Decimal("29.99"), "EUR",
            "https://example.com/ok", "https://example.com/cancel",
        )
        assert session.redirect_url == "https://paypal.com/approve/ORDER-123"
        # Verify decimal string was sent
        payload = transport.send.call_args.kwargs["json"]
        assert payload["purchase_units"][0]["amount"]["value"] == "29.99"

    def test_create_checkout_failure(self):
        body = {"message": "Unauthorized"}
        transport = self._make_transport(401, body)
        provider = PayPalProvider("bad_token", transport=transport)
        with pytest.raises(UserError):
            provider.create_checkout(
                Decimal("10.00"), "USD",
                "https://example.com/ok", "https://example.com/cancel",
            )


class TestGenericProvider:
    def _make_transport(self, status_code: int, body: dict) -> MagicMock:
        t = MagicMock()
        t.send.return_value = HttpResponse(status_code, {}, body)
        return t

    def test_create_checkout_success(self):
        body = {"id": "sess_abc", "redirect_url": "https://pay.example.com/sess_abc"}
        transport = self._make_transport(200, body)
        provider = GenericProvider(
            "https://api.example.com/checkout",
            "https://api.example.com/payments/{payment_id}",
            transport=transport,
        )
        session = provider.create_checkout(
            Decimal("5.00"), "GBP",
            "https://example.com/ok", "https://example.com/cancel",
        )
        assert session.session_id == "sess_abc"

    def test_get_payment(self):
        body = {"status": "succeeded"}
        transport = self._make_transport(200, body)
        provider = GenericProvider(
            "https://api.example.com/checkout",
            "https://api.example.com/payments/{payment_id}",
            transport=transport,
        )
        status = provider.get_payment("pay_123")
        assert status.state == PaymentState.SUCCEEDED
        assert status.payment_id == "pay_123"

class TestDummyProvider:
    def test_create_checkout_returns_session(self):
        from merchants.providers.dummy import DummyProvider
        provider = DummyProvider()
        session = provider.create_checkout(
            Decimal("9.99"), "USD",
            "https://example.com/ok", "https://example.com/cancel",
        )
        assert session.session_id.startswith("dummy_sess_")
        assert "dummy-pay.example.com" in session.redirect_url
        assert session.amount == Decimal("9.99")
        assert session.currency == "USD"
        assert session.provider == "dummy"

    def test_get_payment_returns_terminal_state(self):
        from merchants.providers.dummy import DummyProvider
        provider = DummyProvider()
        status = provider.get_payment("dummy_sess_abc")
        assert status.is_final

    def test_get_payment_always_state(self):
        from merchants.providers.dummy import DummyProvider
        provider = DummyProvider(always_state=PaymentState.SUCCEEDED)
        status = provider.get_payment("any_id")
        assert status.state == PaymentState.SUCCEEDED
        assert status.is_success

    def test_parse_webhook(self):
        import json
        from merchants.providers.dummy import DummyProvider
        provider = DummyProvider()
        payload = json.dumps({"event_type": "payment.done", "payment_id": "pay_xyz"}).encode()
        event = provider.parse_webhook(payload, {})
        assert event.event_type == "payment.done"
        assert event.payment_id == "pay_xyz"
        assert event.provider == "dummy"



def _make_dummy_provider(key: str) -> Provider:
    _key = key

    class _Dummy(Provider):
        key = _key

        def create_checkout(self, *a, **kw):
            raise UserError("not implemented")

        def get_payment(self, pid):
            return None  # type: ignore

        def parse_webhook(self, payload, headers):
            return None  # type: ignore

    return _Dummy()
