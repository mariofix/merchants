# Flask / Quart

**flask-merchants** is the official Flask extension for merchants-sdk. It handles blueprint registration, session storage, webhook routing, and optional Flask-Admin views.

- **Source:** [github.com/mariofix/flask-merchants](https://github.com/mariofix/flask-merchants)
- **PyPI:** `flask-merchants`

---

## Installation

```bash
# Core (Flask + merchants-sdk)
pip install flask-merchants

# With Flask-Admin and SQLAlchemy support
pip install "flask-merchants[admin]"

# With Quart support
pip install "flask-merchants[quart]"
```

---

## Minimal setup

```python
from flask import Flask
from flask_merchants import FlaskMerchants

app = Flask(__name__)
app.config["SECRET_KEY"] = "change-me"
app.config["MERCHANTS_URL_PREFIX"] = "/pay"

ext = FlaskMerchants(app)  # DummyProvider by default
```

This registers the following routes under `/pay`:

| Method | Path | Description |
|---|---|---|
| `GET/POST` | `/pay/checkout` | Initiate a hosted-checkout session |
| `GET` | `/pay/success` | Post-payment success landing |
| `GET` | `/pay/cancel` | Post-payment cancel landing |
| `GET` | `/pay/status/<id>` | Fetch live payment status |
| `POST` | `/pay/webhook` | Generic webhook receiver |
| `POST` | `/pay/webhook/<provider>` | Provider-specific webhook receiver |
| `GET` | `/pay/providers` | List registered providers |

---

## Application factory pattern

```python
from flask import Flask
from flask_merchants import FlaskMerchants

merchants_ext = FlaskMerchants()  # initialise without app

def create_app():
    app = Flask(__name__)
    app.config["MERCHANTS_URL_PREFIX"] = "/pay"
    merchants_ext.init_app(app)
    return app
```

---

## SQLAlchemy-backed payments

By default flask-merchants stores payment sessions in memory. Pass a `db` and a model class to persist them in a database:

```python
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import Integer
from flask_merchants import FlaskMerchants
from flask_merchants.models import PaymentMixin

class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)

class Payment(PaymentMixin, db.Model):
    __tablename__ = "payments"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///payments.db"

ext = FlaskMerchants(app, db=db, models=[Payment])
db.init_app(app)

with app.app_context():
    db.create_all()
```

### Creating a payment from your own route

Once `db=` and `models=` are configured you can create payments directly:

```python
from flask import redirect, url_for

@app.route("/buy/<product_id>", methods=["POST"])
def buy(product_id):
    payment = Payment.create(
        amount="49.99",
        currency="USD",
        provider="stripe",
        success_url=url_for("success", _external=True),
        cancel_url=url_for("cancel", _external=True),
        email=request.form.get("email"),
    )
    return redirect(payment.response_payload["redirect_url"])
```

---

## Registering a real provider

```python
from flask_merchants import FlaskMerchants
from merchants.providers.stripe import StripeProvider
import merchants

merchants.register_provider(StripeProvider(api_key="sk_test_…"))

ext = FlaskMerchants(app)
```

Or configure the provider key via environment variable so the built-in checkout route picks it up automatically:

```bash
MERCHANTS_PROVIDER=stripe
STRIPE_API_KEY=sk_test_...
```

---

## Flask-Admin views

Pass `admin=` to automatically register payment and provider views:

```python
from flask_admin import Admin
from flask_merchants import FlaskMerchants

admin = Admin(app, name="My Shop")
ext = FlaskMerchants(app, db=db, models=[Payment], admin=admin)
# Registers PaymentModelView and ProvidersView under category "Merchants"
```

---

## Webhook handling

Register a provider-specific webhook endpoint:

```
POST /pay/webhook/stripe
POST /pay/webhook/khipu
```

Pass the URL to your provider as the `notify_url`. Set
`MERCHANTS_WEBHOOK_BASE_URL` so the URL can be computed at runtime:

```python
app.config["MERCHANTS_WEBHOOK_BASE_URL"] = "https://yourapp.example.com"
```

```python
from flask_merchants import get_webhook_url
notify_url = get_webhook_url("khipu")  # https://yourapp.example.com/pay/webhook/khipu
```

To verify webhook signatures:

```python
app.config["MERCHANTS_WEBHOOK_SECRET"] = "your-signing-secret"
```

---

## Quart (async)

Install the Quart extra and swap `Flask` for `Quart` — the API is identical:

```bash
pip install "flask-merchants[quart]"
```

```python
from quart import Quart
from flask_merchants import FlaskMerchants

app = Quart(__name__)
ext = FlaskMerchants(app)
```

---

## Configuration reference

| Config key | Default | Description |
|---|---|---|
| `MERCHANTS_URL_PREFIX` | `/merchants` | URL prefix for built-in routes |
| `MERCHANTS_PROVIDER` | `dummy` | Default provider key |
| `MERCHANTS_WEBHOOK_SECRET` | `None` | HMAC secret for signature verification |
| `MERCHANTS_WEBHOOK_BASE_URL` | `None` | Public base URL for `get_webhook_url()` |
| `MERCHANTS_PAYMENT_VIEW_NAME` | `Payments` | Admin nav label for the payments view |
| `MERCHANTS_PROVIDER_VIEW_NAME` | `Providers` | Admin nav label for the providers view |
