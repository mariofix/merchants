"""PayPal provider scaffold.

Minimal scaffold demonstrating provider interface compliance using decimal-string
amount serialization (PayPal's Orders API accepts amounts as strings).
"""

from __future__ import annotations

from decimal import Decimal

from merchants.amount import to_decimal_string
from merchants.errors import ProviderError
from merchants.payments import CheckoutSession, PaymentState, PaymentStatus
from merchants.providers.base import BaseProvider

# Mapping PayPal order statuses to normalized PaymentState
_PAYPAL_STATE_MAP: dict[str, PaymentState] = {
    "CREATED": PaymentState.PENDING,
    "SAVED": PaymentState.PENDING,
    "APPROVED": PaymentState.PENDING,
    "VOIDED": PaymentState.CANCELED,
    "COMPLETED": PaymentState.SUCCEEDED,
    "PAYER_ACTION_REQUIRED": PaymentState.PENDING,
}


class PayPalProvider(BaseProvider):
    """PayPal hosted-checkout provider scaffold.

    Parameters
    ----------
    client_id:
        PayPal REST API client ID.
    client_secret:
        PayPal REST API client secret.
    sandbox:
        When ``True`` (default), use the PayPal sandbox environment.
    """

    def __init__(self, client_id: str, client_secret: str, *, sandbox: bool = True) -> None:
        self.client_id = client_id
        self.client_secret = client_secret
        self.sandbox = sandbox

    def _base_url(self) -> str:
        return "https://api-m.sandbox.paypal.com" if self.sandbox else "https://api-m.paypal.com"

    def create_checkout(
        self,
        amount: Decimal,
        currency: str,
        *,
        return_url: str,
        **kwargs,
    ) -> CheckoutSession:
        """Create a PayPal Order.

        .. note::
            This scaffold raises :class:`~merchants.errors.ProviderError` until
            the real PayPal REST API call is implemented.
        """
        amount_str = to_decimal_string(amount)
        raise ProviderError(
            "PayPalProvider.create_checkout is a scaffold. "
            f"Would POST amount={amount_str} {currency.upper()} to {self._base_url()}. "
            "Wire in the real PayPal SDK or transport to enable."
        )

    def get_payment(self, payment_id: str) -> PaymentStatus:
        """Fetch a PayPal Order status.

        .. note::
            This scaffold raises :class:`~merchants.errors.ProviderError`.
        """
        raise ProviderError(
            "PayPalProvider.get_payment is a scaffold. "
            f"Would GET {self._base_url()}/v2/checkout/orders/{payment_id}."
        )

    @staticmethod
    def normalize_state(paypal_status: str) -> PaymentState:
        """Map a PayPal order status string to :class:`~merchants.payments.PaymentState`."""
        return _PAYPAL_STATE_MAP.get(paypal_status.upper(), PaymentState.UNKNOWN)
