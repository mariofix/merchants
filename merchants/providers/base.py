"""Abstract base provider protocol."""

from __future__ import annotations

from abc import ABC, abstractmethod
from decimal import Decimal

from merchants.payments import CheckoutSession, PaymentStatus


class BaseProvider(ABC):
    """Abstract base class that all payment provider integrations must implement."""

    @abstractmethod
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
            URL the user is redirected to after completing the checkout.
        **kwargs:
            Provider-specific additional parameters.

        Returns
        -------
        CheckoutSession
            Contains the ``id`` and ``redirect_url`` for the created session.
        """

    @abstractmethod
    def get_payment(self, payment_id: str) -> PaymentStatus:
        """Fetch the current status of a payment.

        Parameters
        ----------
        payment_id:
            The provider-assigned payment / session identifier.

        Returns
        -------
        PaymentStatus
            Normalized payment status.
        """
