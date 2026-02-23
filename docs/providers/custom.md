# Custom Provider

Implement the `Provider` abstract base class to integrate any payment gateway with the merchants SDK.

## Minimal Example

```python
from decimal import Decimal
from typing import Any

from merchants.models import CheckoutSession, PaymentState, PaymentStatus, WebhookEvent
from merchants.providers import Provider, UserError


class MyProvider(Provider):
    key = "my_gateway"

    def create_checkout(
        self,
        amount: Decimal,
        currency: str,
        success_url: str,
        cancel_url: str,
        metadata: dict[str, Any] | None = None,
    ) -> CheckoutSession:
        # Call your gateway here; raise UserError on failure
        return CheckoutSession(
            session_id="sess_1",
            redirect_url="https://pay.my-gateway.com/sess_1",
            provider=self.key,
            amount=amount,
            currency=currency,
        )

    def get_payment(self, payment_id: str) -> PaymentStatus:
        return PaymentStatus(
            payment_id=payment_id,
            state=PaymentState.PENDING,
            provider=self.key,
        )

    def parse_webhook(self, payload: bytes, headers: dict[str, str]) -> WebhookEvent:
        from merchants.webhooks import parse_event
        return parse_event(payload, provider=self.key)
```

## Full Example with HTTP Calls

See [`examples/03_custom_provider.py`](https://github.com/mariofix/merchnts-cp/blob/main/examples/03_custom_provider.py) for a complete provider that:

- Wraps a JSON REST API with `requests`.
- Raises `UserError` on non-2xx responses.
- Maps provider-specific status strings to `PaymentState`.
- Parses incoming webhook payloads.

## Required Methods

| Method | Description |
|---|---|
| `create_checkout(...)` | Creates a hosted-checkout session; returns `CheckoutSession` |
| `get_payment(payment_id)` | Retrieves payment status; returns `PaymentStatus` |
| `parse_webhook(payload, headers)` | Parses raw webhook bytes; returns `WebhookEvent` |

## Raising Errors

Always raise `UserError` (not a generic exception) for provider-level failures:

```python
from merchants.providers import UserError

if not resp.ok:
    raise UserError(
        message="Payment declined",
        code=str(resp.status_code),
    )
```

!!! warning "Use `UserError`, not bare exceptions"
    The SDK catches `UserError` and exposes it cleanly to callers. Raising a generic `Exception` or `RuntimeError` will bypass this handling and may surface as an unexpected 500 error in your application.

## Registering Your Provider

Register a provider instance so it can be selected by key string:

```python
from merchants.providers import register_provider

register_provider(MyProvider())

# Now usable by key
from merchants import Client
client = Client(provider="my_gateway")
```

!!! note "Keys must be unique"
    If you call `register_provider` with a provider whose `key` is already registered, the new instance silently overwrites the old one. Use distinct `key` values to avoid conflicts.

## State Normalisation

Use `normalise_state` to convert arbitrary status strings to `PaymentState` values:

```python
from merchants.providers import normalise_state
from merchants.models import PaymentState

state = normalise_state("paid")     # PaymentState.SUCCEEDED
state = normalise_state("pending")  # PaymentState.PENDING
state = normalise_state("xyzzy")    # PaymentState.UNKNOWN
```

Or define your own mapping:

```python
_STATE_MAP = {
    "WAITING": PaymentState.PENDING,
    "APPROVED": PaymentState.SUCCEEDED,
    "DECLINED": PaymentState.FAILED,
}

state = _STATE_MAP.get(raw_status.upper(), normalise_state(raw_status))
```

!!! tip "Prefer explicit state maps"
    If your gateway uses predictable, documented status strings, define an explicit `_STATE_MAP` dictionary as shown above. This makes the mapping visible, testable, and independent of `normalise_state`'s heuristics.
