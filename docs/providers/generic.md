# Generic Provider

The `GenericProvider` connects to any payment gateway that exposes a simple JSON REST API. Configure it with a checkout URL and a payment URL template.

## Usage

```python
from merchants import Client
from merchants.providers.generic import GenericProvider

provider = GenericProvider(
    checkout_url="https://api.example.com/checkout",
    payment_url_template="https://api.example.com/payments/{payment_id}",
)
client = Client(provider=provider)

session = client.payments.create_checkout(
    amount="99.00",
    currency="USD",
    success_url="https://example.com/success",
    cancel_url="https://example.com/cancel",
)
print(session.redirect_url)
```

!!! info "Best suited for simple JSON gateways"
    `GenericProvider` works well for gateways that accept a standard JSON body and return `id` + `redirect_url`. For more complex flows, consider implementing a [custom provider](custom.md).

## With Extra Headers

Pass static headers (e.g. for API key auth) with `extra_headers`:

```python
provider = GenericProvider(
    checkout_url="https://api.example.com/checkout",
    payment_url_template="https://api.example.com/payments/{payment_id}",
    extra_headers={"X-API-Key": "my-secret-key"},
)
```

Or use the built-in [auth strategies](../auth.md) with the `Client`:

```python
from merchants import Client, ApiKeyAuth

client = Client(
    provider=provider,
    auth=ApiKeyAuth("my-secret-key", header="X-API-Key"),
)
```

## Expected Request/Response Format

### Checkout (POST `checkout_url`)

**Request body:**

```json
{
  "amount": "99.00",
  "currency": "USD",
  "success_url": "https://example.com/success",
  "cancel_url": "https://example.com/cancel",
  "metadata": {}
}
```

**Expected response:**

```json
{
  "id": "sess_abc123",
  "redirect_url": "https://pay.example.com/sess_abc123"
}
```

### Payment Status (GET `payment_url_template`)

**Expected response:**

```json
{
  "status": "succeeded"
}
```

## Parameters

| Parameter | Type | Default | Description |
|---|---|---|---|
| `checkout_url` | `str` | required | Full URL to POST checkout requests to |
| `payment_url_template` | `str` | required | URL template for GET payment status; `{payment_id}` is replaced at runtime |
| `transport` | `Transport \| None` | `None` | Custom HTTP transport |
| `extra_headers` | `dict \| None` | `None` | Static headers added to every request |
