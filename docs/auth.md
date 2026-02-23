# Auth Strategies

merchants provides two built-in authentication strategies that inject credentials into request headers. Both implement the `AuthStrategy` abstract base class.

!!! warning "Never hardcode credentials"
    Load API keys and tokens from environment variables (e.g. `os.environ["STRIPE_KEY"]`) or a secrets manager. Never commit them to source control.

## ApiKeyAuth

Sends a static API key in a configurable request header.

```python
from merchants import Client, ApiKeyAuth
from merchants.providers.generic import GenericProvider

client = Client(
    provider=GenericProvider(
        "https://api.example.com/checkout",
        "https://api.example.com/payments/{payment_id}",
    ),
    auth=ApiKeyAuth("my-secret-key", header="X-API-Key"),
)
```

**Parameters:**

| Parameter | Type | Default | Description |
|---|---|---|---|
| `api_key` | `str` | required | The API key value |
| `header` | `str` | `"X-Api-Key"` | Header name to use |

## TokenAuth

Sends a bearer-style token in a configurable header.

```python
from merchants import Client, TokenAuth
from merchants.providers.generic import GenericProvider

client = Client(
    provider=GenericProvider(
        "https://api.example.com/checkout",
        "https://api.example.com/payments/{payment_id}",
    ),
    auth=TokenAuth("my-token"),
    # Sends: Authorization: Bearer my-token
)
```

**Parameters:**

| Parameter | Type | Default | Description |
|---|---|---|---|
| `token` | `str` | required | The token value |
| `header` | `str` | `"Authorization"` | Header name |
| `scheme` | `str` | `"Bearer"` | Prefix placed before the token |

## Custom Auth Strategy

Implement `AuthStrategy` to add custom authentication logic:

```python
from merchants.auth import AuthStrategy


class HmacAuth(AuthStrategy):
    def __init__(self, secret: str) -> None:
        self._secret = secret

    def apply(self, headers: dict[str, str]) -> dict[str, str]:
        import hashlib, hmac, time
        ts = str(int(time.time()))
        sig = hmac.new(self._secret.encode(), ts.encode(), hashlib.sha256).hexdigest()
        headers["X-Timestamp"] = ts
        headers["X-Signature"] = sig
        return headers
```

Pass it to the client:

```python
client = Client(provider=provider, auth=HmacAuth("my-secret"))
```

!!! tip "Auth applies to all requests"
    The auth strategy is applied to every HTTP request the transport makes, including `client.request(...)` calls. No need to set headers manually.
