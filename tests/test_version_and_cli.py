"""Tests for version.py and provider metadata (ProviderInfo, get_info)."""

import json
from unittest.mock import MagicMock

from typer.testing import CliRunner

import merchants
from merchants.cli import app
from merchants.providers import (
    Provider,
    ProviderInfo,
    UserError,
    describe_providers,
    register_provider,
)
from merchants.providers.dummy import DummyProvider
from merchants.providers.generic import GenericProvider
from merchants.providers.paypal import PayPalProvider
from merchants.providers.stripe import StripeProvider
from merchants.transport import HttpResponse
from merchants.version import __version__

# ---------------------------------------------------------------------------
# version.py
# ---------------------------------------------------------------------------


class TestVersion:
    def test_version_is_string(self):
        assert isinstance(__version__, str)

    def test_version_format(self):
        parts = __version__.split(".")
        assert len(parts) == 3
        assert all(p.isdigit() for p in parts)

    def test_version_exported_from_package(self):
        assert merchants.__version__ == __version__


# ---------------------------------------------------------------------------
# ProviderInfo model
# ---------------------------------------------------------------------------


class TestProviderInfo:
    def test_required_fields(self):
        info = ProviderInfo(key="test", name="Test", author="me", version="1.0.0")
        assert info.key == "test"
        assert info.name == "Test"
        assert info.author == "me"
        assert info.version == "1.0.0"
        assert info.description == ""
        assert info.url == ""

    def test_optional_fields(self):
        info = ProviderInfo(
            key="test",
            name="Test",
            author="me",
            version="1.0.0",
            description="A test provider",
            url="https://example.com",
        )
        assert info.description == "A test provider"
        assert info.url == "https://example.com"

    def test_serialises_to_dict(self):
        info = ProviderInfo(key="x", name="X", author="a", version="0.1.0")
        d = info.model_dump()
        assert d["key"] == "x"
        assert "description" in d

    def test_serialises_to_json(self):
        info = ProviderInfo(key="x", name="X", author="a", version="0.1.0")
        parsed = json.loads(info.model_dump_json())
        assert parsed["key"] == "x"


# ---------------------------------------------------------------------------
# Provider.get_info()
# ---------------------------------------------------------------------------


class TestProviderGetInfo:
    def test_dummy_provider_info(self):
        p = DummyProvider()
        info = p.get_info()
        assert isinstance(info, ProviderInfo)
        assert info.key == "dummy"
        assert info.name == "Dummy"
        assert info.author == "merchants team"
        assert info.version == "1.0.0"
        assert info.description != ""

    def test_stripe_provider_info(self):
        t = MagicMock()
        t.send.return_value = HttpResponse(200, {}, {})
        p = StripeProvider("sk_test_key", transport=t)
        info = p.get_info()
        assert info.key == "stripe"
        assert info.name == "Stripe"
        assert info.url == "https://stripe.com"

    def test_paypal_provider_info(self):
        t = MagicMock()
        t.send.return_value = HttpResponse(200, {}, {})
        p = PayPalProvider("token", transport=t)
        info = p.get_info()
        assert info.key == "paypal"
        assert info.name == "PayPal"

    def test_generic_provider_info(self):
        t = MagicMock()
        t.send.return_value = HttpResponse(200, {}, {})
        p = GenericProvider(
            "https://a.com/checkout", "https://a.com/pay/{payment_id}", transport=t
        )
        info = p.get_info()
        assert info.key == "generic"
        assert info.name == "Generic"

    def test_custom_provider_info(self):
        class MyProvider(Provider):
            key = "my_gw"
            name = "My Gateway"
            author = "acme"
            version = "2.3.4"
            description = "Custom gateway"
            url = "https://my-gw.example.com"

            def create_checkout(self, *a, **kw):
                raise UserError("not impl")

            def get_payment(self, pid):
                return None  # type: ignore

            def parse_webhook(self, payload, headers):
                return None  # type: ignore

        info = MyProvider().get_info()
        assert info.key == "my_gw"
        assert info.name == "My Gateway"
        assert info.author == "acme"
        assert info.version == "2.3.4"
        assert info.url == "https://my-gw.example.com"


# ---------------------------------------------------------------------------
# describe_providers()
# ---------------------------------------------------------------------------


class TestDescribeProviders:
    def setup_method(self):
        register_provider(DummyProvider())

    def test_returns_list_of_provider_info(self):
        result = describe_providers()
        assert isinstance(result, list)
        assert all(isinstance(i, ProviderInfo) for i in result)

    def test_includes_registered_provider(self):
        keys = [i.key for i in describe_providers()]
        assert "dummy" in keys


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


runner = CliRunner()


class TestCLIVersion:
    def test_version_command(self):
        result = runner.invoke(app, ["version"])
        assert result.exit_code == 0
        assert __version__ in result.output
        assert "merchants" in result.output


class TestCLIProviders:
    def setup_method(self):
        register_provider(DummyProvider())

    def test_providers_table(self):
        result = runner.invoke(app, ["providers"])
        assert result.exit_code == 0
        assert "dummy" in result.output

    def test_providers_json(self):
        result = runner.invoke(app, ["providers", "--output", "json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert isinstance(data, list)
        keys = [d["key"] for d in data]
        assert "dummy" in keys

    def test_no_providers_registered_message(self, monkeypatch):
        monkeypatch.setattr("merchants.cli.list_providers", lambda: [])
        monkeypatch.setattr("merchants.cli.describe_providers", lambda: [])
        result = runner.invoke(app, ["providers"])
        assert result.exit_code == 0
        assert "No providers" in result.output


class TestCLIInfo:
    def setup_method(self):
        register_provider(DummyProvider())

    def test_info_text(self):
        result = runner.invoke(app, ["info", "dummy"])
        assert result.exit_code == 0
        assert "dummy" in result.output
        assert "Dummy" in result.output
        assert "merchants team" in result.output

    def test_info_json(self):
        result = runner.invoke(app, ["info", "dummy", "--output", "json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["key"] == "dummy"
        assert data["name"] == "Dummy"

    def test_info_unknown_key(self):
        result = runner.invoke(app, ["info", "nonexistent_provider"])
        assert result.exit_code == 1
        assert "nonexistent_provider" in result.output


# ---------------------------------------------------------------------------
# payments checkout
# ---------------------------------------------------------------------------


class TestCLIPaymentsCheckout:
    def test_checkout_dummy_text(self):
        result = runner.invoke(
            app,
            [
                "payments",
                "checkout",
                "--provider",
                "dummy",
                "--amount",
                "19.99",
                "--currency",
                "USD",
                "--success-url",
                "https://example.com/ok",
                "--cancel-url",
                "https://example.com/cancel",
            ],
        )
        assert result.exit_code == 0
        assert "dummy_sess_" in result.output
        assert "19.99" in result.output
        assert "USD" in result.output

    def test_checkout_dummy_json(self):
        result = runner.invoke(
            app,
            [
                "payments",
                "checkout",
                "--provider",
                "dummy",
                "--amount",
                "9.50",
                "--currency",
                "EUR",
                "--success-url",
                "https://example.com/ok",
                "--cancel-url",
                "https://example.com/cancel",
                "--output",
                "json",
            ],
        )
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["provider"] == "dummy"
        assert data["amount"] == "9.50"
        assert data["currency"] == "EUR"
        assert "session_id" in data
        assert "redirect_url" in data

    def test_checkout_with_metadata(self):
        result = runner.invoke(
            app,
            [
                "payments",
                "checkout",
                "--provider",
                "dummy",
                "--amount",
                "5.00",
                "--currency",
                "USD",
                "--success-url",
                "https://example.com/ok",
                "--cancel-url",
                "https://example.com/cancel",
                "--metadata",
                '{"order_id": "ORD-42"}',
                "--output",
                "json",
            ],
        )
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["metadata"].get("order_id") == "ORD-42"

    def test_checkout_invalid_amount(self):
        result = runner.invoke(
            app,
            [
                "payments",
                "checkout",
                "--provider",
                "dummy",
                "--amount",
                "not-a-number",
                "--currency",
                "USD",
                "--success-url",
                "https://example.com/ok",
                "--cancel-url",
                "https://example.com/cancel",
            ],
        )
        assert result.exit_code == 1

    def test_checkout_invalid_metadata_json(self):
        result = runner.invoke(
            app,
            [
                "payments",
                "checkout",
                "--provider",
                "dummy",
                "--amount",
                "5.00",
                "--currency",
                "USD",
                "--success-url",
                "https://example.com/ok",
                "--cancel-url",
                "https://example.com/cancel",
                "--metadata",
                "{bad json}",
            ],
        )
        assert result.exit_code == 1

    def test_checkout_provider_error(self, monkeypatch):
        def _failing_checkout(*a, **kw):
            raise UserError("card declined")

        dummy = DummyProvider()
        monkeypatch.setattr(dummy, "create_checkout", _failing_checkout)
        monkeypatch.setattr("merchants.cli._resolve_provider", lambda _k: dummy)

        result = runner.invoke(
            app,
            [
                "payments",
                "checkout",
                "--provider",
                "dummy",
                "--amount",
                "1.00",
                "--currency",
                "USD",
                "--success-url",
                "https://example.com/ok",
                "--cancel-url",
                "https://example.com/cancel",
            ],
        )
        assert result.exit_code == 1

    def test_checkout_unknown_provider(self):
        result = runner.invoke(
            app,
            [
                "payments",
                "checkout",
                "--provider",
                "no_such_provider",
                "--amount",
                "1.00",
                "--currency",
                "USD",
                "--success-url",
                "https://example.com/ok",
                "--cancel-url",
                "https://example.com/cancel",
            ],
        )
        assert result.exit_code == 1

    def test_checkout_stripe_missing_env(self, monkeypatch):
        monkeypatch.delenv("STRIPE_API_KEY", raising=False)
        result = runner.invoke(
            app,
            [
                "payments",
                "checkout",
                "--provider",
                "stripe",
                "--amount",
                "1.00",
                "--currency",
                "USD",
                "--success-url",
                "https://example.com/ok",
                "--cancel-url",
                "https://example.com/cancel",
            ],
        )
        assert result.exit_code == 1

    def test_checkout_paypal_missing_env(self, monkeypatch):
        monkeypatch.delenv("PAYPAL_ACCESS_TOKEN", raising=False)
        result = runner.invoke(
            app,
            [
                "payments",
                "checkout",
                "--provider",
                "paypal",
                "--amount",
                "1.00",
                "--currency",
                "USD",
                "--success-url",
                "https://example.com/ok",
                "--cancel-url",
                "https://example.com/cancel",
            ],
        )
        assert result.exit_code == 1

    def test_checkout_generic_missing_env(self, monkeypatch):
        monkeypatch.delenv("GENERIC_CHECKOUT_URL", raising=False)
        monkeypatch.delenv("GENERIC_PAYMENT_URL", raising=False)
        result = runner.invoke(
            app,
            [
                "payments",
                "checkout",
                "--provider",
                "generic",
                "--amount",
                "1.00",
                "--currency",
                "USD",
                "--success-url",
                "https://example.com/ok",
                "--cancel-url",
                "https://example.com/cancel",
            ],
        )
        assert result.exit_code == 1


# ---------------------------------------------------------------------------
# payments get
# ---------------------------------------------------------------------------


class TestCLIPaymentsGet:
    def test_get_dummy_text(self):
        result = runner.invoke(
            app,
            ["payments", "get", "pay_abc123", "--provider", "dummy"],
        )
        assert result.exit_code == 0
        assert "pay_abc123" in result.output
        assert "State" in result.output

    def test_get_dummy_json(self):
        result = runner.invoke(
            app,
            [
                "payments",
                "get",
                "pay_abc123",
                "--provider",
                "dummy",
                "--output",
                "json",
            ],
        )
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["payment_id"] == "pay_abc123"
        assert "state" in data
        assert "is_final" in data
        assert "is_success" in data

    def test_get_unknown_provider(self):
        result = runner.invoke(
            app,
            ["payments", "get", "pay_abc", "--provider", "no_such_provider"],
        )
        assert result.exit_code == 1

    def test_get_provider_error(self, monkeypatch):
        def _failing_get(_pid):
            raise UserError("not found")

        dummy = DummyProvider()
        monkeypatch.setattr(dummy, "get_payment", _failing_get)
        monkeypatch.setattr("merchants.cli._resolve_provider", lambda _k: dummy)

        result = runner.invoke(
            app,
            ["payments", "get", "pay_x", "--provider", "dummy"],
        )
        assert result.exit_code == 1

    def test_get_registered_provider(self):
        from merchants.models import PaymentState

        dummy = DummyProvider(always_state=PaymentState.SUCCEEDED)
        register_provider(dummy)

        result = runner.invoke(
            app,
            [
                "payments",
                "get",
                "pay_registered",
                "--provider",
                "dummy",
                "--output",
                "json",
            ],
        )
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["state"] == "succeeded"
        assert data["is_success"] is True


# ---------------------------------------------------------------------------
# payments webhook
# ---------------------------------------------------------------------------


class TestCLIPaymentsWebhook:
    def _payload(self, data: dict) -> bytes:
        return json.dumps(data).encode()

    def test_webhook_from_file_text(self, tmp_path):
        payload = self._payload(
            {
                "event_type": "payment.done",
                "payment_id": "pay_wh1",
                "status": "succeeded",
            }
        )
        p = tmp_path / "webhook.json"
        p.write_bytes(payload)

        result = runner.invoke(
            app,
            ["payments", "webhook", "--file", str(p), "--provider", "dummy"],
        )
        assert result.exit_code == 0
        assert "pay_wh1" in result.output
        assert "payment.done" in result.output

    def test_webhook_from_file_json(self, tmp_path):
        payload = self._payload({"event_type": "order.paid", "payment_id": "pay_wh2"})
        p = tmp_path / "wh.json"
        p.write_bytes(payload)

        result = runner.invoke(
            app,
            [
                "payments",
                "webhook",
                "--file",
                str(p),
                "--provider",
                "dummy",
                "--output",
                "json",
            ],
        )
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert "event_type" in data
        assert "state" in data
        assert "verified" in data
        assert data["verified"] is False

    def test_webhook_signature_valid(self, tmp_path):
        import hashlib
        import hmac as hmac_mod

        secret = "mysecret"
        payload = self._payload({"event_type": "payment.done", "payment_id": "pay_sig"})
        sig = (
            "sha256="
            + hmac_mod.new(secret.encode(), payload, hashlib.sha256).hexdigest()
        )

        p = tmp_path / "signed.json"
        p.write_bytes(payload)

        result = runner.invoke(
            app,
            [
                "payments",
                "webhook",
                "--file",
                str(p),
                "--provider",
                "dummy",
                "--secret",
                secret,
                "--signature",
                sig,
                "--output",
                "json",
            ],
        )
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["verified"] is True

    def test_webhook_signature_invalid(self, tmp_path):
        payload = self._payload({"event_type": "payment.done"})
        p = tmp_path / "bad.json"
        p.write_bytes(payload)

        result = runner.invoke(
            app,
            [
                "payments",
                "webhook",
                "--file",
                str(p),
                "--secret",
                "correct_secret",
                "--signature",
                "sha256=badhash",
            ],
        )
        assert result.exit_code == 1

    def test_webhook_missing_file(self):
        result = runner.invoke(
            app,
            ["payments", "webhook", "--file", "/tmp/no_such_file_xyz.json"],
        )
        assert result.exit_code == 1

    def test_webhook_registered_provider(self, tmp_path):
        register_provider(DummyProvider())
        payload = self._payload(
            {"event_type": "payment.simulated", "payment_id": "pay_rp"}
        )
        p = tmp_path / "wh_reg.json"
        p.write_bytes(payload)

        result = runner.invoke(
            app,
            [
                "payments",
                "webhook",
                "--file",
                str(p),
                "--provider",
                "dummy",
                "--output",
                "json",
            ],
        )
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["provider"] == "dummy"
