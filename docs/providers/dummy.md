# Dummy Provider

The `DummyProvider` is a no-op provider for **local development and testing**. It generates random data and never makes any real HTTP calls.

## Usage

```python
from merchants import Client
from merchants.providers.dummy import DummyProvider

client = Client(provider=DummyProvider())

session = client.payments.create_checkout(
    amount="49.99",
    currency="USD",
    success_url="https://example.com/success",
    cancel_url="https://example.com/cancel",
)
print("Session ID  :", session.session_id)
print("Redirect URL:", session.redirect_url)

status = client.payments.get(session.session_id)
print("State       :", status.state)
```

!!! danger "Not for production"
    `DummyProvider` does not process real payments. Using it in a live environment will cause your users to be redirected to a fake URL and no charge will occur.

## Behaviour

- `create_checkout` returns a `CheckoutSession` with a random `session_id` and a fake redirect URL.
- `get_payment` returns a `PaymentStatus` with a random `PaymentState`.
- `parse_webhook` returns a `WebhookEvent` with `UNKNOWN` state.
- No credentials required.
- No network calls are made.

## When to Use

Use `DummyProvider` when:

- Developing locally without payment credentials.
- Writing unit or integration tests.
- Prototyping a new integration.

!!! tip "Combine with pytest"
    In tests, create a `Client(provider=DummyProvider())` and assert on the returned `CheckoutSession` and `PaymentStatus` objects without needing to mock HTTP calls.

!!! warning
    Never use `DummyProvider` in production. It does not process real payments.
