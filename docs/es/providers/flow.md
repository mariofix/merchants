# Proveedor Flow.cl

`FlowProvider` se integra con [Flow.cl](https://www.flow.cl), un gateway de pagos chileno, a través del paquete [`pyflowcl`](https://pypi.org/project/pyflowcl/).

## Instalación

Instala merchants con el extra `flow`:

```bash
pip install "merchants[flow]"
```

!!! note "Requiere pyflowcl"
    El extra `flow` instala [`pyflowcl`](https://pypi.org/project/pyflowcl/). Si no está instalado, importar `FlowProvider` lanza un `ImportError` con instrucciones de instalación.

## Uso

```python
from merchants import Client
from merchants.providers.flow import FlowProvider

provider = FlowProvider(api_key="TU_API_KEY", api_secret="TU_API_SECRET")
client = Client(provider=provider)

session = client.payments.create_checkout(
    amount="9990",
    currency="CLP",
    success_url="https://example.com/exito",
    cancel_url="https://example.com/cancelar",
    metadata={"order_id": "ord_456"},
)
print(session.redirect_url)  # redirige al usuario a Flow aquí
```

## Estado del Pago

```python
status = client.payments.get("NUMERO_ORDEN_FLOW")

print(status.state)     # ej. PaymentState.SUCCEEDED
print(status.amount)    # ej. Decimal("9990")
print(status.currency)  # "CLP"
```

## Parseo de Webhooks

```python
import merchants

event = merchants.parse_event(payload, provider="flow")
print(event.event_type)   # "payment.notification"
print(event.payment_id)   # Número de orden Flow
print(event.state)        # ej. PaymentState.SUCCEEDED
```

## Parámetros

| Parámetro | Tipo | Por defecto | Descripción |
|---|---|---|---|
| `api_key` | `str` | requerido | API key de Flow.cl |
| `api_secret` | `str` | requerido | API secret de Flow.cl |
| `sandbox` | `bool` | `False` | Usar el entorno sandbox de Flow |

!!! tip "Prueba en sandbox primero"
    Establece `sandbox=True` para dirigir todas las peticiones al entorno sandbox de Flow. Obtén las credenciales de sandbox desde tu [cuenta de comerciante en Flow.cl](https://www.flow.cl).

## Mapeo de Estados

| Estado Flow | `PaymentState` |
|---|---|
| `1` (pendiente) | `PENDING` |
| `2` (pagado) | `SUCCEEDED` |
| `3` (rechazado) | `FAILED` |
| `4` (cancelado) | `CANCELLED` |
