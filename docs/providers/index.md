# Providers

merchants ships with several built-in payment providers and a clean abstract base class to build your own.

## Available Providers

| Provider | Key | Install extra | Description |
|---|---|---|---|
| [`StripeProvider`](stripe.md) | `"stripe"` | – | Stripe Checkout Sessions via minor-unit amounts |
| [`PayPalProvider`](paypal.md) | `"paypal"` | – | PayPal Orders API via decimal-string amounts |
| [`FlowProvider`](flow.md) | `"flow"` | `merchants[flow]` | Flow.cl (Chile) via `pyflowcl` |
| [`KhipuProvider`](khipu.md) | `"khipu"` | `merchants[khipu]` | Khipu (Chile) via `khipu-tools` |
| [`GenericProvider`](generic.md) | `"generic"` | – | Configurable JSON REST endpoints |
| [`DummyProvider`](dummy.md) | `"dummy"` | – | Random data, no API calls — for local dev and testing |

## Provider Registry

Providers can be registered globally by key so they can be looked up later by string:

```python
from merchants import Client, register_provider, list_providers
from merchants.providers.stripe import StripeProvider

# Register once at startup
register_provider(StripeProvider(api_key="sk_test_…"))

# Later, select by key string
client = Client(provider="stripe")

# List all registered providers
print(list_providers())  # ['stripe']
```

!!! info "Registry is process-global"
    Registered providers live for the lifetime of the Python process. Register them once at application startup (e.g. in your app factory or `__init__` module).

## Selecting a Provider

### By instance

Pass a provider instance directly to the client:

```python
from merchants import Client
from merchants.providers.paypal import PayPalProvider

client = Client(provider=PayPalProvider(access_token="token_…"))
```

### By string key

Use a registered provider by its string key:

```python
from merchants import Client

client = Client(provider="stripe")  # must be registered first
```

!!! warning "Provider must be registered first"
    Passing a string key to `Client` without registering the provider first raises a `KeyError`. Call `register_provider(...)` at startup before creating clients by key.

## Custom Providers

See the [Custom Provider](custom.md) guide to integrate any payment gateway by subclassing `Provider`.
