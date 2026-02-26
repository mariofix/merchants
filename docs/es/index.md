# merchants

*SDK de pagos con hosted-checkout independiente del framework para Python. Simple, rápido e independiente del proveedor.*

---

**merchants** es un SDK de Python para integrar flujos de pago con hosted-checkout en cualquier framework web. Tu servidor nunca toca datos de tarjetas — simplemente redirige al usuario a la página de pago del proveedor.

!!! tip "¿Recién empiezas?"
    Ve directamente a la guía de [Inicio Rápido](quickstart.md) para tener un ejemplo funcionando en menos de cinco minutos.

## Características Principales

- **Solo hosted checkout** — redirige a los usuarios a la página de pago del proveedor; ningún dato de tarjeta pasa por tu servidor.
- **Proveedores incluidos** — Stripe, PayPal, [Flow.cl](https://www.flow.cl) y [Khipu](https://khipu.com), más un `DummyProvider` para desarrollo local.
- **Transporte intercambiable** — backend por defecto con `requests.Session`; inyecta cualquier `Transport` para pruebas o clientes HTTP personalizados.
- **Autenticación flexible** — estrategias de auth por API key y token bearer.
- **Modelos Pydantic** — `CheckoutSession`, `PaymentStatus`, `WebhookEvent` con type hints completos.
- **Utilidades de montos** — `to_decimal_string`, `to_minor_units`, `from_minor_units`.
- **Utilidades para webhooks** — verificación de firma HMAC-SHA256 en tiempo constante y parseo de eventos.

---

## Ejemplo Rápido

```python
import merchants
from merchants.providers.stripe import StripeProvider

# 1. Crea un proveedor
stripe = StripeProvider(api_key="sk_test_…")

# 2. Crea un cliente
client = merchants.Client(provider=stripe)

# 3. Crea una sesión de checkout
session = client.payments.create_checkout(
    amount="19.99",
    currency="USD",
    success_url="https://example.com/exito",
    cancel_url="https://example.com/cancelar",
    metadata={"order_id": "ord_123"},
)
print(session.redirect_url)  # redirige al usuario aquí
```

!!! note "Sin datos de tarjeta en tu servidor"
    merchants solo soporta flujos de hosted-checkout. Los datos de la tarjeta se ingresan en la página del proveedor y nunca pasan por tu aplicación.

---

## Proveedores Soportados

| Proveedor | Clave | Extra de instalación | Notas |
|---|---|---|---|
| `StripeProvider` | `"stripe"` | – | Montos en unidades mínimas (centavos) |
| `PayPalProvider` | `"paypal"` | – | Montos como cadena decimal |
| `FlowProvider` | `"flow"` | `merchants[flow]` | Flow.cl (Chile) via `pyflowcl` |
| `KhipuProvider` | `"khipu"` | `merchants[khipu]` | Khipu (Chile) via `khipu-tools` |
| `GenericProvider` | `"generic"` | – | Endpoints REST configurables |
| `DummyProvider` | `"dummy"` | – | Datos aleatorios, sin llamadas a API |

---

## Instalación

```bash
pip install merchants
```

Visita la página de [Instalación](installation.md) para todas las opciones incluyendo los extras de proveedores.

---

## Licencia

MIT
