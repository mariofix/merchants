# Webhooks

merchants provides utilities for verifying webhook signatures and parsing normalised webhook events from payment providers.

## Signature Verification

Use `verify_signature` to confirm that a webhook came from your provider using HMAC-SHA256 constant-time comparison. This prevents timing attacks.

```python
import merchants

try:
    merchants.verify_signature(
        payload=request.body,          # raw bytes
        secret="whsec_…",
        signature=request.headers["Stripe-Signature"],
    )
except merchants.WebhookVerificationError:
    # Reject the request — signature is invalid
    return 400
```

!!! danger "Never skip signature verification"
    Without verification, anyone who knows your webhook endpoint URL can send fake payment-success notifications. Always verify before processing.

### Parameters

| Parameter | Type | Description |
|---|---|---|
| `payload` | `bytes` | Raw request body |
| `secret` | `str` | Webhook secret from your provider dashboard |
| `signature` | `str` | Signature header value from the incoming request |

### `WebhookVerificationError`

Raised when the computed HMAC does not match the provided signature:

```python
from merchants import WebhookVerificationError

try:
    merchants.verify_signature(payload, secret, signature)
except WebhookVerificationError as e:
    print(e)  # "invalid webhook signature"
```

## Event Parsing

Use `parse_event` to parse a raw webhook payload into a normalised `WebhookEvent`:

```python
import merchants

event = merchants.parse_event(request.body, provider="stripe")

print(event.event_type)  # e.g. "payment_intent.succeeded"
print(event.state)       # e.g. PaymentState.SUCCEEDED
print(event.payment_id)  # e.g. "pi_3LHpu2…"
print(event.provider)    # "stripe"
```

!!! note "Best-effort parsing"
    `parse_event` does a best-effort conversion of the raw payload to a `WebhookEvent`. Unknown event types or unrecognised status strings result in `state=PaymentState.UNKNOWN`. Check `event.raw` for the full original payload.

### Parameters

| Parameter | Type | Description |
|---|---|---|
| `payload` | `bytes` | Raw webhook body |
| `provider` | `str` | Provider key (e.g. `"stripe"`, `"paypal"`) |

### `WebhookEvent` Fields

| Field | Type | Description |
|---|---|---|
| `event_id` | `str \| None` | Provider-assigned event ID |
| `event_type` | `str` | Provider-specific event type string |
| `payment_id` | `str \| None` | Associated payment ID |
| `state` | `PaymentState` | Normalised payment state |
| `provider` | `str` | Provider key |
| `raw` | `dict` | Original parsed payload for provider-specific fields |

## Full Webhook Handler Example

Here is a complete webhook handler using Django-style pseudo-code:

```python
import merchants
from merchants import WebhookVerificationError

def webhook_view(request):
    # 1. Verify signature
    try:
        merchants.verify_signature(
            payload=request.body,
            secret=settings.STRIPE_WEBHOOK_SECRET,
            signature=request.headers.get("Stripe-Signature", ""),
        )
    except WebhookVerificationError:
        return HttpResponse(status=400)

    # 2. Parse the event
    event = merchants.parse_event(request.body, provider="stripe")

    # 3. Handle by event type or state
    if event.state == merchants.PaymentState.SUCCEEDED:
        fulfill_order(event.payment_id)
    elif event.state == merchants.PaymentState.FAILED:
        notify_failure(event.payment_id)

    return HttpResponse(status=200)
```

## Using Provider's `parse_webhook`

For provider-specific parsing (including state maps defined in the provider), use the provider's own method via the client:

```python
# Access the provider directly if needed
provider = client._provider
event = provider.parse_webhook(request.body, dict(request.headers))
```

!!! tip "Use `event.raw` for provider-specific fields"
    The `WebhookEvent.raw` field holds the original parsed payload. Access it when you need provider-specific fields that are not covered by the normalised model.
