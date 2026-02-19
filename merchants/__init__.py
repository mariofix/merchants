"""merchants – framework-agnostic payment SDK."""

from merchants.amount import to_decimal_string, to_minor_units
from merchants.auth import ApiKeyAuth, BaseAuth, BearerTokenAuth, NoAuth
from merchants.client import MerchantsClient
from merchants.errors import (
    MerchantsError,
    ParseError,
    ProviderError,
    ProviderNotFoundError,
    TransportError,
    WebhookVerificationError,
)
from merchants.payments import CheckoutSession, PaymentState, PaymentStatus
from merchants.providers import ProviderRegistry, registry
from merchants.result import Failure, Success
from merchants.transport import BaseTransport, RequestsTransport, TransportResponse
from merchants.version import __version__
from merchants.webhook import WebhookEvent, parse_event, verify_signature

__all__ = [
    "__version__",
    # client
    "MerchantsClient",
    # payments
    "CheckoutSession",
    "PaymentState",
    "PaymentStatus",
    # providers
    "ProviderRegistry",
    "registry",
    # result
    "Success",
    "Failure",
    # amount
    "to_decimal_string",
    "to_minor_units",
    # auth
    "BaseAuth",
    "BearerTokenAuth",
    "ApiKeyAuth",
    "NoAuth",
    # transport
    "BaseTransport",
    "RequestsTransport",
    "TransportResponse",
    # webhook
    "WebhookEvent",
    "verify_signature",
    "parse_event",
    # errors
    "MerchantsError",
    "TransportError",
    "ProviderError",
    "ProviderNotFoundError",
    "WebhookVerificationError",
    "ParseError",
]
