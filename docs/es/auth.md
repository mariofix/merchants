# Estrategias de Autenticación

merchants provee dos estrategias de autenticación incorporadas que inyectan credenciales en los headers de las peticiones. Ambas implementan la clase base abstracta `AuthStrategy`.

!!! warning "Nunca hardcodees credenciales"
    Carga las API keys y tokens desde variables de entorno (ej. `os.environ["STRIPE_KEY"]`) o un gestor de secretos. Nunca los incluyas en el código fuente.

## ApiKeyAuth

Envía una API key estática en un header de petición configurable.

```python
from merchants import Client, ApiKeyAuth
from merchants.providers.generic import GenericProvider

client = Client(
    provider=GenericProvider(
        "https://api.example.com/checkout",
        "https://api.example.com/payments/{payment_id}",
    ),
    auth=ApiKeyAuth("mi-clave-secreta", header="X-API-Key"),
)
```

**Parámetros:**

| Parámetro | Tipo | Por defecto | Descripción |
|---|---|---|---|
| `api_key` | `str` | requerido | El valor de la API key |
| `header` | `str` | `"X-Api-Key"` | Nombre del header a usar |

## TokenAuth

Envía un token bearer en un header configurable.

```python
from merchants import Client, TokenAuth
from merchants.providers.generic import GenericProvider

client = Client(
    provider=GenericProvider(
        "https://api.example.com/checkout",
        "https://api.example.com/payments/{payment_id}",
    ),
    auth=TokenAuth("mi-token"),
    # Envía: Authorization: Bearer mi-token
)
```

**Parámetros:**

| Parámetro | Tipo | Por defecto | Descripción |
|---|---|---|---|
| `token` | `str` | requerido | El valor del token |
| `header` | `str` | `"Authorization"` | Nombre del header |
| `scheme` | `str` | `"Bearer"` | Prefijo que se agrega antes del token |

## Estrategia de Auth Personalizada

Implementa `AuthStrategy` para agregar lógica de autenticación personalizada:

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

Pásala al cliente:

```python
client = Client(provider=provider, auth=HmacAuth("mi-secreto"))
```

!!! tip "La auth se aplica a todas las peticiones"
    La estrategia de autenticación se aplica a cada petición HTTP que hace el transporte, incluyendo las llamadas a `client.request(...)`. No es necesario configurar headers manualmente.
