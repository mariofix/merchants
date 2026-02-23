# Transporte Personalizado

El protocolo `Transport` define un único método `send`. Por defecto merchants usa `RequestsTransport`, pero puedes inyectar cualquier cliente HTTP.

## Transporte por Defecto

`RequestsTransport` envuelve una `requests.Session`. Puedes pasar una sesión preconfigurada:

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

!!! tip "Agrega reintentos para producción"
    Envuelve la `requests.Session` por defecto con un adaptador `Retry` (como se muestra arriba) para manejar errores de red transitorios sin ningún cambio en el SDK o en el código de tu proveedor.

## Transporte Personalizado con httpx

```python
from __future__ import annotations
from typing import Any

import httpx
from merchants.transport import HttpResponse, Transport, TransportError


class HttpxTransport(Transport):
    """Transporte basado en httpx.Client."""

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

Usalo con cualquier proveedor:

```python
from merchants import Client
from merchants.providers.dummy import DummyProvider

client = Client(
    provider=DummyProvider(),
    transport=HttpxTransport(httpx.Client(timeout=httpx.Timeout(10.0))),
)
```

## Protocolo Transport

Implementa el ABC `Transport` con un único método `send`:

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

El método `send` debe retornar un `HttpResponse`:

| Campo | Tipo | Descripción |
|---|---|---|
| `status_code` | `int` | Código de estado HTTP |
| `headers` | `dict[str, str]` | Headers de la respuesta |
| `body` | `dict \| list \| str` | Cuerpo JSON parseado o cadena cruda |
| `ok` | `bool` | `True` si `200 <= status_code < 300` (propiedad calculada) |

## Acceso de Bajo Nivel

Usa `client.request` para hacer llamadas HTTP arbitrarias a través del transporte configurado:

```python
response = client.request("GET", "https://api.stripe.com/v1/balance")
print(response.status_code, response.body)
```

!!! note "El transporte es compartido"
    `client.request` usa el mismo transporte (y estrategia de auth) configurado en el `Client`. Esto es útil para llamadas a la API que no están cubiertas por la abstracción del proveedor.
