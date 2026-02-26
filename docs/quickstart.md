# Quick Start

This guide shows the essential steps to go from installation to a working payment redirect in minutes.

## 1. Install merchants

```bash
pip install merchants
```

## 2. Choose a Provider

Pick a payment provider that matches your gateway. For local development, use the `DummyProvider` — it requires no credentials and generates random data.

!!! info "No credentials for local dev"
    `DummyProvider` simulates a provider without making any real API calls. Use it while building or testing your integration.

=== "Dummy (local dev)"

    ```python
    from merchants.providers.dummy import DummyProvider

    provider = DummyProvider()
    ```

=== "Stripe"

    ```python
    from merchants.providers.stripe import StripeProvider

    provider = StripeProvider(api_key="sk_test_…")
    ```

=== "PayPal"

    ```python
    from merchants.providers.paypal import PayPalProvider

    provider = PayPalProvider(access_token="ACCESS_TOKEN")
    ```

## 3. Create a Client

```python
import merchants

client = merchants.Client(provider=provider)
```

## 4. Create a Checkout Session

```python
try:
    session = client.payments.create_checkout(
        amount="19.99",
        currency="USD",
        success_url="https://example.com/success",
        cancel_url="https://example.com/cancel",
        metadata={"order_id": "ord_123"},
    )
    # Redirect the user to the payment page
    print(session.redirect_url)
except merchants.UserError as e:
    print("Payment setup failed:", e)
```

!!! tip
    In a real web application you would return a redirect response to `session.redirect_url` instead of printing it.

!!! warning "Always handle `UserError`"
    `UserError` is raised when the provider rejects the request (e.g. invalid currency, bad credentials). Catch it and return a meaningful response to your user instead of letting it propagate as a 500 error.

## 5. Check Payment Status

After the user completes (or cancels) the payment, retrieve the updated status:

```python
status = client.payments.get(session.session_id)

print(status.state)       # e.g. PaymentState.SUCCEEDED
print(status.is_final)    # True once payment is terminal
print(status.is_success)  # True only when SUCCEEDED
```

!!! note
    Use `status.is_final` to determine if polling can stop. A final state means no further transitions are expected.

## 6. Handle Webhooks

Verify incoming webhook signatures and parse the event:

```python
import merchants

# Verify HMAC-SHA256 signature (raises WebhookVerificationError on failure)
merchants.verify_signature(
    payload=request.body,
    secret="whsec_…",
    signature=request.headers["Stripe-Signature"],
)

# Parse and normalise the event
event = merchants.parse_event(request.body, provider="stripe")
print(event.event_type)  # e.g. "payment_intent.succeeded"
print(event.state)       # e.g. PaymentState.SUCCEEDED
```

!!! danger "Never skip signature verification"
    Always call `verify_signature` before processing a webhook. Without it, anyone can send a fake payment-success notification to your endpoint.

## Next Steps

- Learn about all [Providers](providers/index.md) and their specific options.
- Explore [Auth Strategies](auth.md) for API key and token auth.
- See how to plug in a [Custom Transport](transport.md).
- Read the full [API Reference](api-reference/index.md).
