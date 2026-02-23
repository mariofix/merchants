"""Main Client entry point for the merchants SDK."""

from __future__ import annotations

from decimal import Decimal
from typing import Any

from merchants.auth import AuthStrategy
from merchants.models import CheckoutSession, PaymentStatus
from merchants.providers import Provider, get_provider
from merchants.transport import HttpResponse, RequestsTransport, Transport


class PaymentsResource:
    """Resource object exposed as ``client.payments``.

    Provides hosted-checkout creation and payment status retrieval.
    """

    def __init__(self, provider: Provider) -> None:
        self._provider = provider

    def create_checkout(
        self,
        amount: Decimal | int | float | str,
        currency: str,
        success_url: str,
        cancel_url: str,
        metadata: dict[str, Any] | None = None,
    ) -> CheckoutSession:
        """Create a hosted-checkout session.

        Args:
            amount: Payment amount; converted to :class:`~decimal.Decimal`.
            currency: ISO-4217 currency code (e.g. ``"USD"``).
            success_url: URL to redirect to after successful payment.
            cancel_url: URL to redirect to when the user cancels.
            metadata: Optional key-value pairs passed to the provider.

        Returns:
            :class:`~merchants.models.CheckoutSession` – redirect the user to
            ``session.redirect_url``.

        Raises:
            :class:`~merchants.providers.UserError`: If the provider rejects the request.
        """
        return self._provider.create_checkout(
            Decimal(str(amount)),
            currency,
            success_url,
            cancel_url,
            metadata,
        )

    def get(self, payment_id: str) -> PaymentStatus:
        """Retrieve and normalise the status of a payment.

        Args:
            payment_id: Provider-specific payment / session identifier.

        Returns:
            :class:`~merchants.models.PaymentStatus`.
        """
        return self._provider.get_payment(payment_id)


class Client:
    """Main entry point for the merchants SDK.

    Args:
        provider: A :class:`~merchants.providers.Provider` instance **or**
            a registered provider key string (e.g. ``"stripe"``).
        auth: Optional :class:`~merchants.auth.AuthStrategy` to apply to
            low-level requests made via :meth:`request`.
        transport: Optional custom :class:`~merchants.transport.Transport`.
            Defaults to :class:`~merchants.transport.RequestsTransport`.
        base_url: Optional base URL used by :meth:`request`.

    Example::

        from merchants import Client
        from merchants.providers.stripe import StripeProvider

        client = Client(provider=StripeProvider(api_key="sk_test_…"))
        result = client.payments.create_checkout(
            amount="19.99",
            currency="USD",
            success_url="https://example.com/success",
            cancel_url="https://example.com/cancel",
        )
    """

    def __init__(
        self,
        provider: Provider | str,
        *,
        auth: AuthStrategy | None = None,
        transport: Transport | None = None,
        base_url: str = "",
    ) -> None:
        self._provider = get_provider(provider)
        self._auth = auth
        self._transport = transport or RequestsTransport()
        self._base_url = base_url.rstrip("/")
        self.payments = PaymentsResource(self._provider)

    def request(
        self,
        method: str,
        path: str,
        *,
        json: Any = None,
        params: dict[str, str] | None = None,
        headers: dict[str, str] | None = None,
        timeout: float = 30.0,
    ) -> HttpResponse:
        """Low-level HTTP escape hatch for provider-specific calls.

        Applies configured auth if present and uses the configured transport.

        Raises:
            :class:`~merchants.transport.TransportError`: On network failure.
        """
        hdrs: dict[str, str] = dict(headers or {})
        if self._auth:
            hdrs = self._auth.apply(hdrs)

        url = f"{self._base_url}{path}" if self._base_url else path
        return self._transport.send(
            method,
            url,
            headers=hdrs,
            json=json,
            params=params,
            timeout=timeout,
        )
