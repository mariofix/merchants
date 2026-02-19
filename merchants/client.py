"""MerchantsClient – the main entry point for the SDK."""

from __future__ import annotations

from decimal import Decimal
from typing import Union

from merchants.auth import BaseAuth, NoAuth
from merchants.errors import ProviderNotFoundError
from merchants.payments import CheckoutSession, PaymentStatus
from merchants.providers import ProviderRegistry, registry as _default_registry
from merchants.providers.base import BaseProvider
from merchants.transport import BaseTransport, RequestsTransport


class MerchantsClient:
    """High-level client for the merchants SDK.

    Parameters
    ----------
    provider:
        Either a provider name string (looked up in *registry*) or a
        :class:`~merchants.providers.base.BaseProvider` instance directly.
    registry:
        The :class:`~merchants.providers.ProviderRegistry` to use for name
        lookup.  Defaults to the module-level :data:`merchants.providers.registry`.
    transport:
        Custom :class:`~merchants.transport.BaseTransport`.  Defaults to
        :class:`~merchants.transport.RequestsTransport`.
    auth:
        :class:`~merchants.auth.BaseAuth` strategy applied to outgoing
        requests.  Defaults to :class:`~merchants.auth.NoAuth`.

    Examples
    --------
    Using a pre-registered provider name::

        from merchants.client import MerchantsClient
        client = MerchantsClient(provider="mock")
        session = client.create_checkout(
            amount=Decimal("19.99"),
            currency="USD",
            return_url="https://example.com/return",
        )
        print(session.redirect_url)

    Passing a provider instance directly::

        from merchants.client import MerchantsClient
        from merchants.providers.mock import MockProvider
        client = MerchantsClient(provider=MockProvider())
    """

    def __init__(
        self,
        *,
        provider: Union[str, BaseProvider],
        registry: ProviderRegistry = _default_registry,
        transport: BaseTransport | None = None,
        auth: BaseAuth | None = None,
    ) -> None:
        if isinstance(provider, str):
            self._provider: BaseProvider = registry.get(provider)
        else:
            self._provider = provider

        self._transport: BaseTransport = transport or RequestsTransport()
        self._auth: BaseAuth = auth or NoAuth()

    @property
    def provider(self) -> BaseProvider:
        """The active :class:`~merchants.providers.base.BaseProvider`."""
        return self._provider

    def create_checkout(
        self,
        amount: Decimal,
        currency: str,
        *,
        return_url: str,
        **kwargs,
    ) -> CheckoutSession:
        """Create a hosted-checkout session.

        Parameters
        ----------
        amount:
            Payment amount as :class:`~decimal.Decimal`.
        currency:
            ISO 4217 currency code (e.g., ``"USD"``).
        return_url:
            URL to redirect to after the checkout completes.
        **kwargs:
            Extra parameters forwarded to the provider.
        """
        return self._provider.create_checkout(
            amount,
            currency,
            return_url=return_url,
            **kwargs,
        )

    def get_payment(self, payment_id: str) -> PaymentStatus:
        """Fetch the current status of a payment by its provider-assigned ID."""
        return self._provider.get_payment(payment_id)
