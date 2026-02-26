# Custom Transport

The `Transport` protocol defines a single `send` method. By default merchants uses `RequestsTransport`, but you can inject any HTTP client.

## Default Transport

`RequestsTransport` wraps a `requests.Session`. You can pass a pre-configured session:

```python
import requests
from requests.adapters import HTTPAdapter, Retry
from merchants import Client, RequestsTransport
from merchants.providers.stripe import StripeProvider

session = requests.Session()
retry = Retry(total=3, backoff_factor=0.5)
session.mount("https://", HTTPAdapter(max_retries=retry))

client = Client(
    provider=StripeProvider(api_key="sk_test_…"),
    transport=RequestsTransport(session=session),
)
```

!!! tip "Add retries for production"
    Wrap the default `requests.Session` with a `Retry` adapter (as shown above) to handle transient network errors without any changes to the SDK or your provider code.

## Custom Transport with httpx

```python
from __future__ import annotations
from typing import Any

import httpx
from merchants.transport import HttpResponse, Transport, TransportError


class HttpxTransport(Transport):
    """Transport backed by httpx.Client."""

    def __init__(self, client: httpx.Client | None = None) -> None:
        self._client = client or httpx.Client()

    def send(
        self,
        method: str,
        url: str,
        *,
        headers: dict[str, str] | None = None,
        json: Any = None,
        params: dict[str, str] | None = None,
        timeout: float = 30.0,
    ) -> HttpResponse:
        try:
            resp = self._client.request(
                method, url,
                headers=headers, json=json, params=params, timeout=timeout,
            )
        except httpx.RequestError as exc:
            raise TransportError(str(exc)) from exc

        try:
            body = resp.json()
        except ValueError:
            body = resp.text

        return HttpResponse(
            status_code=resp.status_code,
            headers=dict(resp.headers),
            body=body,
        )
```

Use it with any provider:

```python
from merchants import Client
from merchants.providers.dummy import DummyProvider

client = Client(
    provider=DummyProvider(),
    transport=HttpxTransport(httpx.Client(timeout=httpx.Timeout(10.0))),
)
```

## Transport Protocol

Implement the `Transport` ABC with a single `send` method:

```python
from abc import ABC, abstractmethod
from typing import Any
from merchants.transport import HttpResponse


class Transport(ABC):
    @abstractmethod
    def send(
        self,
        method: str,
        url: str,
        *,
        headers: dict[str, str] | None = None,
        json: Any = None,
        params: dict[str, str] | None = None,
        timeout: float = 30.0,
    ) -> HttpResponse:
        ...
```

### `HttpResponse`

The `send` method must return an `HttpResponse`:

| Field | Type | Description |
|---|---|---|
| `status_code` | `int` | HTTP status code |
| `headers` | `dict[str, str]` | Response headers |
| `body` | `dict \| list \| str` | Parsed JSON body or raw string |
| `ok` | `bool` | `True` if `200 <= status_code < 300` (computed property) |

## Low-level Escape Hatch

Use `client.request` to make arbitrary HTTP calls through the configured transport:

```python
response = client.request("GET", "https://api.stripe.com/v1/balance")
print(response.status_code, response.body)
```

!!! note "Transport is shared"
    `client.request` uses the same transport (and auth strategy) configured on the `Client`. This is useful for one-off API calls that are not covered by the provider abstraction.
