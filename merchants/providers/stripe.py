"""Stripe provider scaffold.

This is a minimal scaffold demonstrating:
- Amount conversion to minor units (cents) as required by the Stripe API.
- Provider interface compliance.

A full implementation would use the ``stripe`` Python library or call the
Stripe REST API directly via the SDK's transport layer.
"""

from __future__ import annotations

from decimal import Decimal

from merchants.amount import to_minor_units
from merchants.errors import ProviderError
from merchants.payments import CheckoutSession, PaymentState, PaymentStatus
from merchants.providers.base import BaseProvider

# Mapping Stripe payment-intent statuses to normalized PaymentState
_STRIPE_STATE_MAP: dict[str, PaymentState] = {
    "requires_payment_method": PaymentState.PENDING,
    "requires_confirmation": PaymentState.PENDING,
    "requires_action": PaymentState.PENDING,
    "processing": PaymentState.PENDING,
    "requires_capture": PaymentState.PENDING,
    "canceled": PaymentState.CANCELED,
    "succeeded": PaymentState.SUCCEEDED,
}


class StripeProvider(BaseProvider):
    """Stripe hosted-checkout provider scaffold.

    Parameters
    ----------
    api_key:
        Stripe secret API key (``sk_live_...`` or ``sk_test_...``).
    currency_exponent:
        Number of decimal places for the target currency (default ``2`` for
        most currencies; use ``0`` for zero-decimal currencies like JPY).
    """

    def __init__(self, api_key: str, *, currency_exponent: int = 2) -> None:
        self.api_key = api_key
        self.currency_exponent = currency_exponent

    def _amount_for_stripe(self, amount: Decimal) -> int:
        """Return the amount in minor units (cents) as required by Stripe."""
        return to_minor_units(amount, exponent=self.currency_exponent)

    def create_checkout(
        self,
        amount: Decimal,
        currency: str,
        *,
        return_url: str,
        **kwargs,
    ) -> CheckoutSession:
        """Create a Stripe Checkout Session.

        .. note::
            This scaffold raises :class:`~merchants.errors.ProviderError` until
            a real Stripe API call is wired in.  Replace the body with a call to
            ``stripe.checkout.Session.create(...)`` or to the SDK transport.
        """
        minor_units = self._amount_for_stripe(amount)
        raise ProviderError(
            "StripeProvider.create_checkout is a scaffold. "
            f"Would POST amount={minor_units} {currency.upper()} to Stripe. "
            "Wire in the real Stripe SDK or transport to enable."
        )

    def get_payment(self, payment_id: str) -> PaymentStatus:
        """Fetch a Stripe Payment-Intent status.

        .. note::
            This scaffold raises :class:`~merchants.errors.ProviderError`.
        """
        raise ProviderError(
            "StripeProvider.get_payment is a scaffold. "
            f"Would GET /v1/payment_intents/{payment_id} from Stripe."
        )

    @staticmethod
    def normalize_state(stripe_status: str) -> PaymentState:
        """Map a Stripe payment-intent status string to :class:`~merchants.payments.PaymentState`."""
        return _STRIPE_STATE_MAP.get(stripe_status, PaymentState.UNKNOWN)
