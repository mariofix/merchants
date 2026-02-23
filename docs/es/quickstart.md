# Inicio Rápido

Esta guía muestra los pasos esenciales para pasar de la instalación a un redirect de pago funcionando en minutos.

## 1. Instala merchants

```bash
pip install merchants
```

## 2. Elige un Proveedor

Elige el proveedor de pagos que corresponda a tu gateway. Para desarrollo local, usa el `DummyProvider` — no requiere credenciales y genera datos aleatorios.

!!! info "Sin credenciales para desarrollo local"
    `DummyProvider` simula un proveedor sin hacer llamadas reales a ninguna API. Úsalo mientras construyes o pruebas tu integración.

=== "Dummy (desarrollo local)"

    ```python
    from merchants.providers.dummy import DummyProvider

    provider = DummyProvider()
    ```

=== "Stripe"

    ```python
    from merchants.providers.stripe import StripeProvider

    provider = StripeProvider(api_key="sk_test_…")
    ```

=== "PayPal"

    ```python
    from merchants.providers.paypal import PayPalProvider

    provider = PayPalProvider(access_token="ACCESS_TOKEN")
    ```

## 3. Crea un Cliente

```python
import merchants

client = merchants.Client(provider=provider)
```

## 4. Crea una Sesión de Checkout

```python
try:
    session = client.payments.create_checkout(
        amount="19.99",
        currency="USD",
        success_url="https://example.com/exito",
        cancel_url="https://example.com/cancelar",
        metadata={"order_id": "ord_123"},
    )
    # Redirige al usuario a la página de pago
    print(session.redirect_url)
except merchants.UserError as e:
    print("Error al configurar el pago:", e)
```

!!! tip
    En una aplicación web real retornarías una respuesta de redirección a `session.redirect_url` en lugar de imprimirlo.

!!! warning "Siempre maneja `UserError`"
    `UserError` se lanza cuando el proveedor rechaza la solicitud (ej. moneda inválida, credenciales incorrectas). Captúralo y retorna una respuesta significativa al usuario en lugar de dejarlo propagarse como un error 500.

## 5. Consulta el Estado del Pago

Después de que el usuario completa (o cancela) el pago, obtén el estado actualizado:

```python
status = client.payments.get(session.session_id)

print(status.state)       # ej. PaymentState.SUCCEEDED
print(status.is_final)    # True cuando el pago está en estado terminal
print(status.is_success)  # True solo cuando el pago fue exitoso
```

!!! note
    Usa `status.is_final` para determinar si puedes detener el polling. Un estado final significa que no se esperan más transiciones.

## 6. Procesa Webhooks

Verifica las firmas de los webhooks entrantes y parsea el evento:

```python
import merchants

# Verifica la firma HMAC-SHA256 (lanza WebhookVerificationError si falla)
merchants.verify_signature(
    payload=request.body,
    secret="whsec_…",
    signature=request.headers["Stripe-Signature"],
)

# Parsea y normaliza el evento
event = merchants.parse_event(request.body, provider="stripe")
print(event.event_type)  # ej. "payment_intent.succeeded"
print(event.state)       # ej. PaymentState.SUCCEEDED
```

!!! danger "Nunca omitas la verificación de firma"
    Siempre llama a `verify_signature` antes de procesar un webhook. Sin esto, cualquiera puede enviar notificaciones falsas de pago exitoso a tu endpoint.

## Próximos Pasos

- Conoce todos los [Proveedores](providers/index.md) y sus opciones específicas.
- Explora las [Estrategias de Autenticación](auth.md) para auth por API key y token.
- Aprende a conectar un [Transporte Personalizado](transport.md).
- Lee la [Referencia de API](api-reference/index.md) completa.
