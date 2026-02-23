"""merchants – framework-agnostic hosted-checkout payment SDK."""
from __future__ import annotations

from merchants.amount import from_minor_units, to_decimal_string, to_minor_units
from merchants.auth import ApiKeyAuth, AuthStrategy, TokenAuth
from merchants.client import Client, PaymentsResource
from merchants.models import (
    CheckoutSession,
    PaymentState,
    PaymentStatus,
    WebhookEvent,
)
from merchants.providers import (
    Provider,
    ProviderInfo,
    UserError,
    describe_providers,
    get_provider,
    list_providers,
    normalise_state,
    register_provider,
)
from merchants.transport import (
    HttpResponse,
    RequestsTransport,
    Transport,
    TransportError,
)
from merchants.version import __version__
from merchants.webhooks import WebhookVerificationError, parse_event, verify_signature

__all__ = [
    # Client
    "Client",
    "PaymentsResource",
    # Auth
    "ApiKeyAuth",
    "AuthStrategy",
    "TokenAuth",
    # Models
    "CheckoutSession",
    "PaymentState",
    "PaymentStatus",
    "WebhookEvent",
    # Providers
    "Provider",
    "ProviderInfo",
    "UserError",
    "describe_providers",
    "get_provider",
    "list_providers",
    "normalise_state",
    "register_provider",
    # Transport
    "HttpResponse",
    "RequestsTransport",
    "Transport",
    "TransportError",
    # Amount
    "from_minor_units",
    "to_decimal_string",
    "to_minor_units",
    # Webhooks
    "WebhookVerificationError",
    "parse_event",
    "verify_signature",
    # Version
    "__version__",
]
