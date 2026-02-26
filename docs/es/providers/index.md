# Proveedores

merchants incluye varios proveedores de pago integrados y una clase base abstracta limpia para crear los tuyos.

## Proveedores Disponibles

| Proveedor | Clave | Extra de instalación | Descripción |
|---|---|---|---|
| [`StripeProvider`](stripe.md) | `"stripe"` | – | Sesiones de Checkout de Stripe con montos en unidades mínimas |
| [`PayPalProvider`](paypal.md) | `"paypal"` | – | API de Órdenes de PayPal con montos como cadena decimal |
| [`FlowProvider`](flow.md) | `"flow"` | `merchants[flow]` | Flow.cl (Chile) via `pyflowcl` |
| [`KhipuProvider`](khipu.md) | `"khipu"` | `merchants[khipu]` | Khipu (Chile) via `khipu-tools` |
| [`GenericProvider`](generic.md) | `"generic"` | – | Endpoints REST JSON configurables |
| [`DummyProvider`](dummy.md) | `"dummy"` | – | Datos aleatorios, sin llamadas a API — para desarrollo local y pruebas |

## Registro de Proveedores

Los proveedores se pueden registrar globalmente por clave para consultarlos después como cadena de texto:

```python
from merchants import Client, register_provider, list_providers
from merchants.providers.stripe import StripeProvider

# Registra una vez al iniciar la aplicación
register_provider(StripeProvider(api_key="sk_test_…"))

# Después, selecciona por clave de texto
client = Client(provider="stripe")

# Lista todos los proveedores registrados
print(list_providers())  # ['stripe']
```

!!! info "El registro es global al proceso"
    Los proveedores registrados viven durante todo el ciclo de vida del proceso Python. Regístralos una sola vez al iniciar la aplicación (ej. en tu factory de app o módulo `__init__`).

## Selección de Proveedor

### Por instancia

Pasa una instancia de proveedor directamente al cliente:

```python
from merchants import Client
from merchants.providers.paypal import PayPalProvider

client = Client(provider=PayPalProvider(access_token="token_…"))
```

### Por clave de texto

Usa un proveedor registrado por su clave de texto:

```python
from merchants import Client

client = Client(provider="stripe")  # debe estar registrado primero
```

!!! warning "El proveedor debe registrarse primero"
    Pasar una clave de texto a `Client` sin registrar el proveedor primero lanza un `KeyError`. Llama a `register_provider(...)` al inicio antes de crear clientes por clave.

## Proveedores Personalizados

Consulta la guía de [Proveedor Personalizado](custom.md) para integrar cualquier gateway de pago subclaseando `Provider`.
